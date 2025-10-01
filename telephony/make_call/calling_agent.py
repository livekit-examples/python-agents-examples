"""
---
title: Outbound Calling Agent
category: telephony
tags: [telephony, outbound-calls, survey, ice-cream-preference]
difficulty: beginner
description: Agent that makes outbound calls to ask about ice cream preferences
demonstrates:
  - Outbound call agent configuration
  - Goal-oriented conversation flow
  - Focused questioning strategy
  - Brief and direct interaction patterns
  - Automatic greeting generation
---
"""

import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import openai, silero, deepgram

load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / '.env')

logger = logging.getLogger("calling-agent")
logger.setLevel(logging.INFO)

class SimpleAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are calling someone on the phone. Your goal is to know if they prefer
                chocolate or vanilla ice cream. That's the only question you should ask, and
                you should get right to the point. Say something like "Hello, I'm calling to
                ask you a question about ice cream. Do you prefer chocolate or vanilla?"
            """,
            stt="assemblyai/universal-streaming",
            llm="openai/gpt-4.1-mini",
            tts="cartesia/sonic-2:6f84f4b8-58a2-430c-8c79-688dad597532",
            vad=silero.VAD.load()
        )

    async def on_enter(self):
        self.session.generate_reply()

async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=SimpleAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))