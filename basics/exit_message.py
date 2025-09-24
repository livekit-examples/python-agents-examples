"""
---
title: Exit Message
category: basics
tags: [exit, message, openai, deepgram]
difficulty: beginner
description: Shows how to use the `on_exit` method to take an action when the agent exits.
demonstrates:
  - Use the `on_exit` method to take an action when the agent exits
---
"""
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import openai, silero, deepgram
from livekit.agents.llm import function_tool

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

logger = logging.getLogger("listen-and-respond")
logger.setLevel(logging.INFO)

class GoodbyeAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent.
                When the user wants to stop talking to you, use the end_session function to close the session.
            """,
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o"),
            tts=openai.TTS(),
            vad=silero.VAD.load()
        )

    @function_tool
    async def end_session(self):
        """When the user wants to stop talking to you, use this function to close the session."""
        await self.session.drain()
        await self.session.aclose()

    async def on_exit(self):
        await self.session.say("Goodbye!")

async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=GoodbyeAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))