from __future__ import annotations

import asyncio
import inspect
import logging
import os
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

from livekit import rtc
from livekit.agents import get_job_context
from livekit.rtc._proto import video_frame_pb2 as proto_video

try:
    from PIL import Image
except ImportError:  # pragma: no cover - pillow is expected to be available in agents
    Image = None  # type: ignore[assignment]

from .registry import register
from .runtime import get_state

Captioner = Callable[[Any], Awaitable[str | None] | str | None]


class SupportsModel(Protocol):
    def caption(self, image: Any) -> dict[str, Any]:
        ...


class _MoondreamCaptioner:
    def __init__(self, api_key: str | None = None) -> None:
        import moondream as md  # type: ignore[import-not-found]

        self._model: SupportsModel = md.vl(api_key=api_key)

    async def __call__(self, image: Any) -> str | None:
        loop = asyncio.get_running_loop()

        def _run() -> str | None:
            try:
                response = self._model.caption(image)
            except Exception as exc:  # pragma: no cover - external dependency
                logging.getLogger("livekit.ext.image_processor").warning(
                    "Moondream caption request failed: %s", exc
                )
                return None
            if not isinstance(response, dict):
                return None
            caption = response.get("caption")
            return caption if isinstance(caption, str) else None

        return await loop.run_in_executor(None, _run)


class _ImageProcessorHelper:
    def __init__(
        self,
        *,
        logger: logging.Logger,
        captioner: Captioner | None,
        auto_append: bool,
        append_format: str,
    ) -> None:
        self._logger = logger
        self._captioner = captioner
        self._auto_append = auto_append
        self._append_format = append_format
        self._agent: Any | None = None
        self._room: rtc.Room | None = None
        self._video_stream: rtc.VideoStream | None = None
        self._tasks: set[asyncio.Task[Any]] = set()
        self._latest_frame: rtc.VideoFrame | None = None
        self._frame_lock = asyncio.Lock()
        self.last_caption: str | None = None
        self._started = False

    @property
    def is_ready(self) -> bool:
        return Image is not None and self._captioner is not None

    def set_captioner(self, captioner: Captioner | None) -> None:
        self._captioner = captioner

    async def describe_latest(self) -> str | None:
        if not self.is_ready:
            return None
        frame = await self._consume_latest_frame()
        if frame is None:
            return None
        return await self._describe_frame(frame)

    def attach(self, agent: Any) -> None:
        if self._agent is agent:
            return
        self._agent = agent
        self._patch_methods(agent)

    async def on_enter(self) -> None:
        if not self.is_ready:
            return
        if self._started:
            return
        self._started = True

        ctx = get_job_context()
        if not ctx or not getattr(ctx, "room", None):
            self._logger.warning("ImageProcessor: no active room in job context")
            return
        room = ctx.room
        self._room = room

        self._prime_existing_tracks(room)
        self._watch_new_tracks(room)

        ctx.add_shutdown_callback(self.close)

    async def on_user_turn_completed(
        self,
        turn_ctx: Any | None = None,
        new_message: Any | None = None,
        *extra_args: Any,
        **extra_kwargs: Any,
    ) -> None:
        if not self._auto_append or not self.is_ready:
            return
        if new_message is None:
            if extra_args:
                new_message = extra_args[0]
            else:
                new_message = extra_kwargs.get("new_message")
        if new_message is None:
            return
        frame = await self._consume_latest_frame()
        if frame is None:
            return
        caption = await self._describe_frame(frame)
        if not caption:
            return
        self.last_caption = caption
        try:
            content = getattr(new_message, "content", None)
            if isinstance(content, list):
                content.append(self._append_format.format(caption=caption))
        except Exception:  # pragma: no cover - defensive append
            self._logger.exception("ImageProcessor: failed to append caption to message")

    def close(self) -> None:
        self._latest_frame = None
        if self._video_stream is not None:
            try:
                self._video_stream.close()
            except Exception:  # pragma: no cover - clean up best effort
                self._logger.exception("ImageProcessor: failed to close video stream")
        self._video_stream = None

        for task in list(self._tasks):
            task.cancel()
        self._tasks.clear()
        self._started = False

    def _patch_methods(self, agent: Any) -> None:
        if getattr(agent, "_livekit_ext_image_processor_patched", False):
            return

        setattr(agent, "_livekit_ext_image_processor_patched", True)

        self._patch_method(agent, "on_enter", self.on_enter, run_after=True)
        self._patch_method(
            agent, "on_user_turn_completed", self.on_user_turn_completed, run_after=False
        )

    def _patch_method(
        self,
        agent: Any,
        method_name: str,
        handler: Callable[..., Awaitable[None]],
        *,
        run_after: bool,
    ) -> None:
        import types

        original = getattr(agent, method_name, None)

        if original is None:

            async def _noop(*_: Any, **__: Any) -> None:
                return None

            bound_original = _noop
        else:
            bound_original = original  # method already bound

        async def _wrapper(_: Any, *args: Any, **kwargs: Any) -> Any:
            result: Any = None
            if not run_after:
                await handler(*args, **kwargs)

            if bound_original is not None:
                result = bound_original(*args, **kwargs)
                if inspect.isawaitable(result):
                    result = await result

            if run_after:
                await handler(*args, **kwargs)
            return result

        setattr(agent, method_name, types.MethodType(_wrapper, agent))

    def _prime_existing_tracks(self, room: rtc.Room) -> None:
        participants = getattr(room, "remote_participants", {})
        if not participants:
            return
        for publication in self._iter_video_publications(participants):
            track = getattr(publication, "track", None)
            if track:
                self._create_video_stream(track)
                break

    def _watch_new_tracks(self, room: rtc.Room) -> None:
        @room.on("track_subscribed")
        def _on_track_subscribed(
            track: rtc.Track,
            publication: rtc.RemoteTrackPublication,
            _: rtc.RemoteParticipant,
        ) -> None:
            if track.kind == rtc.TrackKind.KIND_VIDEO:
                self._create_video_stream(track)

    def _create_video_stream(self, track: rtc.Track) -> None:
        self._logger.debug(
            "ImageProcessor: attaching to video track %s", getattr(track, "sid", "<unknown>")
        )
        self._close_stream()
        stream = rtc.VideoStream(track)
        self._video_stream = stream

        async def _read_stream() -> None:
            try:
                async for event in stream:
                    async with self._frame_lock:
                        self._latest_frame = event.frame
            except asyncio.CancelledError:
                pass
            except Exception:  # pragma: no cover - stream errors are logged
                self._logger.exception("ImageProcessor: video stream read failed")
            finally:
                if self._video_stream is stream:
                    self._video_stream = None

        task = asyncio.create_task(_read_stream(), name="image-processor-frame-reader")
        task.add_done_callback(lambda t: self._tasks.discard(t))
        self._tasks.add(task)

    def _close_stream(self) -> None:
        if self._video_stream is not None:
            try:
                self._video_stream.close()
            except Exception:  # pragma: no cover
                self._logger.exception("ImageProcessor: failed to close previous stream")
        self._video_stream = None
        for task in list(self._tasks):
            task.cancel()
        self._tasks.clear()

    async def _consume_latest_frame(self) -> rtc.VideoFrame | None:
        async with self._frame_lock:
            frame = self._latest_frame
            self._latest_frame = None
            return frame

    async def _describe_frame(self, frame: rtc.VideoFrame) -> str | None:
        if Image is None or self._captioner is None:
            return None
        try:
            rgb_frame = frame.convert(proto_video.VideoBufferType.RGB24)
            image = Image.frombytes(
                "RGB",
                (rgb_frame.width, rgb_frame.height),
                rgb_frame.data.tobytes(),
            )
        except Exception:
            self._logger.exception("ImageProcessor: unable to convert frame to image")
            return None

        try:
            result = self._captioner(image)
            if inspect.isawaitable(result):
                result = await result
        except Exception:  # pragma: no cover - captioners are user-provided
            self._logger.exception("ImageProcessor: captioner raised an exception")
            return None

        if result:
            caption = str(result).strip()
            return caption or None
        return None

    def _iter_video_publications(self, participants: dict[str, Any]):
        for participant in participants.values():
            publications = getattr(participant, "track_publications", {}).values()
            for publication in publications:
                if getattr(publication, "track", None) and getattr(
                    publication.track, "kind", None
                ) == rtc.TrackKind.KIND_VIDEO:
                    yield publication


def _build_default_captioner() -> Captioner | None:
    if Image is None:
        logging.getLogger("livekit.ext.image_processor").warning(
            "ImageProcessor: pillow is not installed; image captions disabled"
        )
        return None
    try:
        import moondream as md  # type: ignore[import-not-found]
    except ImportError:
        logging.getLogger("livekit.ext.image_processor").warning(
            "ImageProcessor: moondream is not installed; provide a custom captioner to enable image descriptions"
        )
        return None
    api_key = os.getenv("MOONDREAM_API_KEY") or None
    try:
        md.vl  # type: ignore[attr-defined]
    except AttributeError:  # pragma: no cover - unexpected sdk shape
        logging.getLogger("livekit.ext.image_processor").warning(
            "ImageProcessor: unexpected moondream SDK shape; custom captioner required"
        )
        return None
    return _MoondreamCaptioner(api_key=api_key)


@register("image_processor")
class ImageProcessor:
    def __init__(
        self,
        *,
        captioner: Captioner | None = None,
        auto_append: bool = True,
        append_format: str = "[Image description: {caption}]",
        logger: logging.Logger | None = None,
    ) -> None:
        self._provided_captioner = captioner
        self._auto_append = auto_append
        self._append_format = append_format
        self._logger = logger or logging.getLogger("livekit.ext.image_processor")

    def install(self, agent: Any, **_: Any) -> None:
        state = get_state(agent)
        captioner = self._provided_captioner or _build_default_captioner()

        helper = _ImageProcessorHelper(
            logger=self._logger,
            captioner=captioner,
            auto_append=self._auto_append,
            append_format=self._append_format,
        )
        state.helpers.image_processor = helper

        helper.attach(agent)
