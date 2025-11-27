"""
---
title: Change Agent Instructions
category: basics
tags: [instructions, assemblyai, openai, cartesia]
difficulty: beginner
description: Shows how to change the instructions of an agent.
demonstrates:
  - Changing agent instructions after the agent has started using `update_instructions`
---
"""

import logging
import re
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, Agent, AgentSession, inference
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("change-agent-instructions")
logger.setLevel(logging.INFO)

class ChangeInstructionsAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond.
            """,
            stt=inference.STT(
                model="assemblyai/universal-streaming",
                language="en"
            ),
            llm=inference.LLM(
                model="openai/gpt-5-mini",
                provider="openai",
            ),
            tts=inference.TTS(
                model="cartesia/sonic-3",
                voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
            ),
            vad=silero.VAD.load()
        )

    async def on_enter(self):
        # Treat any participant name containing 4 consecutive digits as a phone number.
        if self.session.participant.name and re.search(r"\d{4}", self.session.participant.name):
            await self.update_instructions("""
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
