"""
---
title: Simple Call Answering Agent
category: telephony
tags: [telephony, call-handling, basic-agent, voice-interaction]
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
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import openai, deepgram, silero

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

class SimpleAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent.
            """,
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o"),
            tts=openai.TTS(),
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