"""
---
title: Uninterruptable Agent
category: basics
tags: [interruptions, allow_interruptions, agent_configuration]
difficulty: beginner
description: Agent configured to complete responses without user interruptions
demonstrates:
  - Setting allow_interruptions=False in agent configuration
  - Testing interruption handling behavior
  - Agent-initiated conversation with on_enter
---
"""

from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import silero

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

class UninterruptableAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice who is not interruptable.
            """,
            stt="assemblyai/universal-streaming",
            llm="openai/gpt-4.1-mini",
            tts="cartesia/sonic-2:6f84f4b8-58a2-430c-8c79-688dad597532",
            allow_interruptions=False,
            vad=silero.VAD.load()
        )

    async def on_enter(self):
        self.session.generate_reply(user_input="Say something somewhat long and boring so I can test if you're interruptable.")

async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=UninterruptableAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))