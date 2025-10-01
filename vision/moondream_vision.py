"""
---
title: Moondream Vision Agent
category: vision
tags: [moondream, vision]
difficulty: intermediate
description: Moondream Vision Agent
demonstrates:
  - Adding vision capabilities to an agent when the LLM does not have vision capabilities
---
"""

import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image
import moondream as md
import os
from livekit import rtc
from livekit.rtc._proto import video_frame_pb2 as proto_video
from livekit.agents import JobContext, WorkerOptions, cli, get_job_context
from livekit.agents.llm import function_tool, ImageContent, ChatContext, ChatMessage
from livekit.agents.voice import Agent, AgentSession, RunContext
from livekit.plugins import silero

logger = logging.getLogger("vision-agent")
logger.setLevel(logging.INFO)

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

class VisionAgent(Agent):
    def __init__(self) -> None:
        self._latest_frame = None
        self._video_stream = None
        self._tasks = []
        self._md_model = md.vl(api_key=os.getenv("MOONDREAM_API_KEY"))
        super().__init__(
            instructions="""
                You are an assistant communicating through voice with vision capabilities.
                You will be given a description of an image, and you can talk to the user about the images that are being shown.
            """,
            stt="assemblyai/universal-streaming",
            llm="openai/gpt-4.1-mini",
            tts="cartesia/sonic-2:6f84f4b8-58a2-430c-8c79-688dad597532",
            vad=silero.VAD.load()
        )

    async def on_enter(self):
        room = get_job_context().room

        # Find the first video track (if any) from the remote participant
        if room.remote_participants:
            remote_participant = list(room.remote_participants.values())[0]
            video_tracks = [
                publication.track
                for publication in list(remote_participant.track_publications.values())
                if publication.track and publication.track.kind == rtc.TrackKind.KIND_VIDEO
            ]
            if video_tracks:
                self._create_video_stream(video_tracks[0])

        # Watch for new video tracks not yet published
        @room.on("track_subscribed")
        def on_track_subscribed(track: rtc.Track, publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
            if track.kind == rtc.TrackKind.KIND_VIDEO:
                self._create_video_stream(track)

    def _send_frame_to_moondream(self, frame: rtc.VideoFrame) -> str | None:
        try:
            rgb_frame = frame.convert(proto_video.VideoBufferType.RGB24)
            image = Image.frombytes(
                "RGB",
                (rgb_frame.width, rgb_frame.height),
                rgb_frame.data.tobytes(),
            )
            caption = self._md_model.caption(image).get("caption")
            if caption:
                logger.info("Moondream caption: %s", caption)
            return caption
        except Exception as exc:
            logger.error("Error sending frame to Moondream: %s", exc)
            return None

    async def on_user_turn_completed(self, turn_ctx: ChatContext, new_message: ChatMessage) -> None:
        # Add the latest video frame, if any, to the new message
        if self._latest_frame:
            # Send the frame to Moondream
            caption = self._send_frame_to_moondream(self._latest_frame)
            if caption:
                # Add the image description as text content to the message
                new_message.content.append(f"[Image description: {caption}]")
            self._latest_frame = None

    # Helper method to buffer the latest video frame from the user's track
    def _create_video_stream(self, track: rtc.Track):
        # Close any existing stream (we only want one at a time)
        if self._video_stream is not None:
            self._video_stream.close()

        # Create a new stream to receive frames
        self._video_stream = rtc.VideoStream(track)
        async def read_stream():
            async for event in self._video_stream:
                # Store the latest frame for use later
                self._latest_frame = event.frame

        # Store the async task
        task = asyncio.create_task(read_stream())
        task.add_done_callback(lambda t: self._tasks.remove(t))
        self._tasks.append(task)

async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=VisionAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
