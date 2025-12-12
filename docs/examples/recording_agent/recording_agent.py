"""
---
title: Recording Agent
category: egress
tags: [recording, deepgram, openai, cartesia]
difficulty: intermediate
description: Shows how to create an agent that can record the input to a room and save it to a file.
demonstrates:
  - Using egress to record the input to a room
---
"""

import logging
from dotenv import load_dotenv
from livekit import api
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession, inference
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("recording-agent")
logger.setLevel(logging.INFO)

class RecordingAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond.
            """
        )

    async def on_enter(self):
        self.session.generate_reply()

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

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

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-5-mini"),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(agent=RecordingAgent(), room=ctx.room)
    await ctx.connect()

    await lkapi.aclose()

if __name__ == "__main__":
    cli.run_app(server)
