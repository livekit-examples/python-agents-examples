"""
---
title: Recording Agent
category: egress
tags: [recording]
difficulty: intermediate
description: Shows how to create an agent that can record the input to a room and save it to a file.
demonstrates:
  - Using egress to record the input to a room
---
"""

import logging
from pathlib import Path
from dotenv import load_dotenv
from livekit import api
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import silero

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

logger = logging.getLogger("recording-agent")
logger.setLevel(logging.INFO)

class RecordingAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond.
            """,
            stt="assemblyai/universal-streaming",
            llm="openai/gpt-4.1-mini",
            tts="cartesia/sonic-2:6f84f4b8-58a2-430c-8c79-688dad597532",
            vad=silero.VAD.load()
        )

    async def on_enter(self):
        self.session.generate_reply()

async def entrypoint(ctx: JobContext):
    file_contents = ""
    with open("/path/to/credentials.json", "r") as f:
      file_contents = f.read()

    req = api.RoomCompositeEgressRequest(
        room_name="my-room",
        layout="speaker",
        preset=api.EncodingOptionsPreset.H264_720P_30,
        audio_only=False,
        segment_outputs=[api.SegmentedFileOutput(
            filename_prefix="my-output",
            playlist_name="my-playlist.m3u8",
            live_playlist_name="my-live-playlist.m3u8",
            segment_duration=5,
            gcp=api.GCPUpload(
                credentials=file_contents,
                bucket="<my-bucket>",
            ),
        )],
    )
    lkapi = api.LiveKitAPI()
    res = await lkapi.egress.start_room_composite_egress(req)
    session = AgentSession()

    await session.start(
        agent=RecordingAgent(),
        room=ctx.room
    )

    await lkapi.aclose()

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))