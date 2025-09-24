"""
---
title: Cartesia TTS
category: pipeline-tts
tags: [pipeline-tts, openai, deepgram]
difficulty: intermediate
description: Shows how to use the Cartesia TTS model.
demonstrates:
  - Using the Cartesia TTS model.
---
"""
import logging
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit import rtc
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import deepgram, openai, cartesia, silero

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

class CartesiaAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice. You're helping me test ... yourself ... since you're the AI agent. 
                Don't use any unpronouncable characters.
            """,
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o"),
            tts=cartesia.TTS(
                sample_rate=44100,
                model="sonic",
                voice="87bc56aa-ab01-4baa-9071-77d497064686"
            ),
            vad=silero.VAD.load()
        )
    
    async def on_enter(self):
        await self.session.say(f"Hi there! Is there anything I can help you with?")

async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=CartesiaAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))