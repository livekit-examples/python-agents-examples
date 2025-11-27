"""
---
title: Simple Call Answering Agent
category: telephony
tags: [telephony, assemblyai, openai, cartesia]
difficulty: beginner
description: Basic agent for handling incoming phone calls with simple conversation
demonstrates:
  - Simple telephony agent setup
  - Basic call handling workflow
  - Standard STT/LLM/TTS configuration
  - Automatic greeting generation on entry
  - Clean agent session lifecycle
---
"""

import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, Agent, AgentSession, inference
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("answer-call")
logger.setLevel(logging.INFO)

class SimpleAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent.
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
        # Generate initial greeting
        self.session.generate_reply()

async def entrypoint(ctx: JobContext):
    session = AgentSession()
    agent = SimpleAgent()

    await session.start(
        agent=agent,
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
