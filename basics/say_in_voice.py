"""
---
title: Function Tool Voice Switching Agent
category: basics
tags: [tts, voice-switching, function-tools, inworld, deepgram, openai]
difficulty: beginner
description: Demonstrates how to create an agent that can dynamically switch between different voices during a conversation using function tools.
demonstrates:
  - Dynamic TTS voice switching
  - Function tool integration
  - Multiple TTS provider support (Inworld)
---
"""

import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.llm import function_tool
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import silero, inworld

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

logger = logging.getLogger("say-in-voice")
logger.setLevel(logging.INFO)

class SayPhraseInVoiceAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are an agent that can say phrases in different voices.
            """,
            stt="assemblyai/universal-streaming",
            llm="openai/gpt-4.1-mini",
            tts=inworld.TTS(voice="Ashley"),
            vad=silero.VAD.load()
        )

    async def say_phrase_in_voice(self, phrase, voice="Hades"):
        self.tts.update_options(voice=voice)
        await self.session.say(phrase)
        self.tts.update_options(voice="Ashley")

    @function_tool
    async def say_phrase_in_voice_tool(self, phrase: str, voice: str = "Ashley"):
        """Say a phrase in a specific voice"""
        await self.say_phrase_in_voice(phrase, voice)

    async def on_enter(self):
        self.session.generate_reply()

async def entrypoint(ctx: JobContext):
    await ctx.connect()

    session = AgentSession()

    await session.start(
        agent=SayPhraseInVoiceAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))