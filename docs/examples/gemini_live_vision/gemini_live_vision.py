"""
---
title: Gemini Realtime Agent with Live Vision
category: realtime
tags: [gemini_realtime, live_vision, google]
difficulty: beginner
description: Minimal Gemini Realtime model agent setup with live vision capabilities
demonstrates:
  - Gemini Realtime model basic usage
  - Live vision capabilities
  - Session-based generation
  - VAD with Silero
---
"""

import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, AgentServer, cli, RoomInputOptions
from livekit.plugins import silero, google

load_dotenv()

logger = logging.getLogger("gemini-live-vision")
logger.setLevel(logging.INFO)


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="You are a helpful voice AI assistant that can see the world around you.")


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        llm=google.beta.realtime.RealtimeModel(
            model="gemini-2.5-flash-native-audio-preview-09-2025",
            proactivity=True,
            enable_affective_dialog=True
        ),
        vad=ctx.proc.userdata["vad"],
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(video_enabled=True),
    )
    await ctx.connect()

    await session.generate_reply()


if __name__ == "__main__":
    cli.run_app(server)
