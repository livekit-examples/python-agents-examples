from __future__ import annotations

import asyncio
import dataclasses
import functools
import inspect
import json
import uuid
from typing import Any, Awaitable, Callable, TypeVar

from livekit.agents import AgentSession

from .log import log
from .registry import register
from .runtime import get_state

RpcHandler = Callable[[Any], Awaitable[Any] | Any]
T = TypeVar("T")


def _decode_payload(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, (bytes, bytearray)):
        try:
            return value.decode("utf-8")
        except Exception as exc:  # pragma: no cover - extremely rare branch
            log.warning("failed to decode payload bytes", exc_info=exc)
            return None
    return str(value)


class _RPCHelper:
    """Lightweight helper that wraps LiveKit RPC utilities."""

    def __init__(self) -> None:
        self._ctx: Any | None = None
        self._session: Any | None = None
        self._room: Any | None = None
        self._default_identity: str | None = None
        self._pending: list[tuple[str, RpcHandler]] = []
        self._retry_handle: asyncio.TimerHandle | None = None

    def bind(
        self,
        *,
        ctx: Any | None = None,
        session: Any | None = None,
        room: Any | None = None,
        default_identity: str | None = None,
    ) -> None:
        if ctx is not None:
            self._ctx = ctx
        if session is not None:
            self._session = session
        if room is not None:
            self._room = room
        if default_identity is not None:
            self._default_identity = default_identity
        self._flush_pending()

    @property
    def ctx(self) -> Any | None:
        return self._ctx

    @property
    def session(self) -> Any | None:
        return self._session

    @property
    def room(self) -> Any | None:
        if self._room is not None:
            return self._room
        if self._ctx is not None:
            return getattr(self._ctx, "room", None)
        return None

    @property
    def local_participant(self) -> Any | None:
        room = self.room
        if not room:
            return None
        try:
            return getattr(room, "local_participant", None)
        except Exception:
            return None

    def participants(self) -> dict[str, Any]:
        room = self.room
        participants = getattr(room, "remote_participants", None) if room else None
        if isinstance(participants, dict):
            return participants
        return {}

    def default_identity(self) -> str | None:
        if self._default_identity:
            return self._default_identity
        participants = self.participants().values()
        participant = next(iter(participants), None)
        return getattr(participant, "identity", None)

    async def send(
        self,
        method: str,
        payload: Any = None,
        *,
        identity: str | None = None,
    ) -> None:
        participant = self.local_participant
        if participant is None:
            raise RuntimeError("RPC helper is not bound to a room")

        target_identity = identity or self.default_identity()
        if target_identity is None:
            raise RuntimeError(
                "RPC helper could not determine a destination identity; "
                "pass one explicitly to send()"
            )

        payload_value: Any
        if payload is None:
            payload_value = ""
        elif isinstance(payload, (str, bytes, bytearray)):
            payload_value = payload
        else:
            payload_value = json.dumps(payload)

        await participant.perform_rpc(
            destination_identity=target_identity,
            method=method,
            payload=payload_value,
        )

    def register(self, method: str, handler: RpcHandler | None = None):
        if handler is None:
            def decorator(func: RpcHandler):
                self.register(method, func)
                return func

            return decorator

        participant = self.local_participant
        if participant is None:
            self._pending.append((method, handler))
            return handler

        participant.register_rpc_method(method, handler)
        return handler

    def load_json(self, rpc_data: Any) -> Any:
        payload = getattr(rpc_data, "payload", None)
        text = _decode_payload(payload)
        if text in (None, ""):
            return None

        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON payload: {text!r}") from exc

    def payload_text(self, rpc_data: Any) -> str | None:
        payload = getattr(rpc_data, "payload", None)
        return _decode_payload(payload)

    def set_default_identity(self, identity: str | None) -> None:
        self._default_identity = identity

    def _flush_pending(self) -> None:
        if not self._pending:
            return
        participant = self.local_participant
        if participant is None:
            self._schedule_flush_retry()
            return
        if self._retry_handle:
            self._retry_handle.cancel()
            self._retry_handle = None
        for method, handler in self._pending:
            participant.register_rpc_method(method, handler)
        self._pending.clear()

    def _schedule_flush_retry(self) -> None:
        if not self._pending:
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        if self._retry_handle and not self._retry_handle.cancelled():
            return
        self._retry_handle = loop.call_later(0.2, self._retry_flush)

    def _retry_flush(self) -> None:
        self._retry_handle = None
        self._flush_pending()


def _ensure_session_patched() -> None:
    if getattr(AgentSession.start, "__livekit_rpc_original__", None):
        return

    original_start = AgentSession.start

    async def patched_start(self: AgentSession, *args: Any, **kwargs: Any):
        agent = kwargs.get("agent") or (args[0] if args else None)
        room = kwargs.get("room")
        if room is None and len(args) > 1:
            room = args[1]

        if agent is not None:
            helper = getattr(get_state(agent).helpers, "rpc", None)
            if helper is not None:
                helper.bind(session=self, room=room)

        return await original_start(self, *args, **kwargs)

    patched_start.__livekit_rpc_original__ = original_start  # type: ignore[attr-defined]
    AgentSession.start = patched_start  # type: ignore[assignment]


def rpc_call(
    topic: str,
    *,
    model: type[Any] | None = None,
    id_field: str | None = "id",
):
    if not topic:
        raise ValueError("rpc_call requires a topic")

    def decorator(func: Callable[..., Awaitable[Any]]):
        if not inspect.iscoroutinefunction(func):
            raise TypeError("rpc_call can only decorate async functions")

        @functools.wraps(func)
        async def wrapper(self, *args: Any, **kwargs: Any):
            helper = getattr(get_state(self).helpers, "rpc", None)
            if helper is None:
                raise RuntimeError("rpc helper is not installed on this agent")

            payload_args = list(args)
            payload_arg = payload_args.pop(0) if payload_args else None
            if payload_args:
                raise TypeError("rpc_call methods accept at most one positional payload argument")

            payload_kwargs = dict(kwargs)
            if payload_arg is None and "payload" in payload_kwargs:
                payload_arg = payload_kwargs.pop("payload")

            payload_obj, payload_dict = _coerce_payload(
                model,
                payload_arg,
                payload_kwargs,
                id_field,
            )

            try:
                await helper.send(topic, payload_dict)
            except Exception:
                log.exception("failed to send rpc payload", extra={"topic": topic})
                raise

            return await func(self, payload_obj)

        wrapper.__rpc_topic__ = topic  # type: ignore[attr-defined]
        wrapper.__rpc_model__ = model  # type: ignore[attr-defined]
        return wrapper

    return decorator


@register("rpc")
class RPC:
    """Registers RPC helper utilities on the agent."""

    name = "rpc"

    def install(self, agent: Any, **_: Any) -> None:
        _ensure_session_patched()
        state = get_state(agent)
        helpers = state.helpers
        if getattr(helpers, "rpc", None) is None:
            helpers.rpc = _RPCHelper()
def _ensure_id(mapping: dict[str, Any], *, field: str | None) -> None:
    if not field:
        return
    if mapping.get(field):
        return
    mapping[field] = str(uuid.uuid4())


def _maybe_dataclass(cls: type[Any] | None) -> bool:
    return bool(cls and dataclasses.is_dataclass(cls))


def _coerce_payload(
    model: type[T] | None,
    arg: Any,
    kwargs: dict[str, Any],
    id_field: str | None,
) -> tuple[Any, dict[str, Any]]:
    if _maybe_dataclass(model):
        payload_obj: Any
        if arg is not None:
            if isinstance(arg, model):
                if kwargs:
                    raise TypeError("rpc_call methods do not accept both payload and kwargs")
                payload_obj = arg
            elif isinstance(arg, dict):
                payload_obj = model(**arg)
            else:
                raise TypeError(f"expected {model.__name__} or dict payload, got {type(arg)!r}")
        else:
            payload_obj = model(**kwargs)
        payload_dict = dataclasses.asdict(payload_obj)
        _ensure_id(payload_dict, field=id_field)
        if id_field and hasattr(payload_obj, id_field) and not getattr(payload_obj, id_field):
            setattr(payload_obj, id_field, payload_dict[id_field])
        return payload_obj, payload_dict

    payload: Any
    if arg is not None:
        if kwargs:
            raise TypeError("rpc_call methods do not accept both payload and kwargs")
        if isinstance(arg, dict):
            payload = dict(arg)
        else:
            raise TypeError("rpc_call without model expects dict payload or keyword args")
    else:
        payload = dict(kwargs)

    if not isinstance(payload, dict):
        raise TypeError("payload must be a mapping for rpc_call without model")

    _ensure_id(payload, field=id_field)
    return payload, payload
