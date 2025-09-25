"""
---
title: Gemini Realtime Agent with Live Vision
category: realtime
tags: [gemini_realtime, live_vision]
difficulty: beginner
description: Minimal Gemini Realtime model agent setup with live vision capabilities
demonstrates:
  - Gemini Realtime model basic usage
  - Live vision capabilities
  - Session-based generation
  - VAD with Silero
---
"""

from dotenv import load_dotenv
from pathlib import Path
from livekit import agents
from livekit.agents import RoomInputOptions
from livekit.agents.voice import AgentSession, Agent
from livekit.plugins import (
    silero,
    google
)

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="You are a helpful voice AI assistant that can see the world around you.")

async def entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        llm=google.beta.realtime.RealtimeModel(
            model="gemini-2.5-flash-native-audio-preview-09-2025",
            proactivity=True,
            enable_affective_dialog=True
        ),
        vad=silero.VAD.load()
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            video_enabled=True
        ),
    )

    await session.generate_reply()

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))