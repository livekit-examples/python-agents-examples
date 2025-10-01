"""
---
title: Change Agent Instructions
category: basics
tags: [instructions, openai, deepgram]
difficulty: beginner
description: Shows how to change the instructions of an agent.
demonstrates:
  - Changing agent instructions after the agent has started using `update_instructions`
---
"""

import logging
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import silero

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

logger = logging.getLogger("change-agent-instructions")
logger.setLevel(logging.INFO)

class ChangeInstructionsAgent(Agent):
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
        if self.session.participant.name.startswith("sip"):
            self.update_instructions("""
                You are a helpful agent speaking on the phone.
            """)
        self.session.generate_reply()

async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=ChangeInstructionsAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))