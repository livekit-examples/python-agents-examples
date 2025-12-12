"""
---
title: Moondream Vision Agent
category: vision
tags: [moondream, vision, deepgram, openai, cartesia]
difficulty: intermediate
description: Moondream Vision Agent
demonstrates:
  - Adding vision capabilities to an agent when the LLM does not have vision capabilities
---
"""

import asyncio
import logging
import os
from dotenv import load_dotenv
from PIL import Image
import moondream as md
from livekit import rtc
from livekit.rtc._proto import video_frame_pb2 as proto_video
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession, inference, get_job_context
from livekit.agents.llm import ChatContext, ChatMessage
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("vision-agent")
logger.setLevel(logging.INFO)

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
            """
        )

    async def on_enter(self):
        room = get_job_context().room

        if room.remote_participants:
            remote_participant = list(room.remote_participants.values())[0]
            video_tracks = [
                publication.track
                for publication in list(remote_participant.track_publications.values())
                if publication.track and publication.track.kind == rtc.TrackKind.KIND_VIDEO
            ]
            if video_tracks:
                self._create_video_stream(video_tracks[0])

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
        if self._latest_frame:
            caption = self._send_frame_to_moondream(self._latest_frame)
            if caption:
                new_message.content.append(f"[Image description: {caption}]")
            self._latest_frame = None

    def _create_video_stream(self, track: rtc.Track):
        if self._video_stream is not None:
            self._video_stream.close()

        self._video_stream = rtc.VideoStream(track)
        async def read_stream():
            async for event in self._video_stream:
                self._latest_frame = event.frame

        task = asyncio.create_task(read_stream())
        task.add_done_callback(lambda t: self._tasks.remove(t))
        self._tasks.append(task)

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-5-mini"),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(agent=VisionAgent(), room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
