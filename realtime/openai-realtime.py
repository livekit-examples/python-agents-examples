"""
---
title: Basic OpenAI Realtime Agent
category: realtime
tags: [openai_realtime, minimal_setup]
difficulty: beginner
description: Minimal OpenAI Realtime model agent setup
demonstrates:
  - OpenAI Realtime model basic usage
  - Minimal agent configuration
  - Session-based generation
  - VAD with Silero
---
"""

from dotenv import load_dotenv
from pathlib import Path
from livekit import agents
from livekit.agents.voice import AgentSession, Agent
from livekit.plugins import (
    openai,
    silero
)

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="You are a helpful voice AI assistant.")

async def entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        llm=openai.realtime.RealtimeModel(),
        vad=silero.VAD.load()
    )

    await session.start(
        room=ctx.room,
        agent=Assistant()
    )

    await session.generate_reply()

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))