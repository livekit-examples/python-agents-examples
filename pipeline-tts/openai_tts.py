"""
---
title: OpenAI TTS
category: pipeline-tts
tags: [pipeline-tts, openai, deepgram]
difficulty: intermediate
description: Shows how to use the OpenAI TTS model.
demonstrates:
  - Using the OpenAI TTS model.
---
"""
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import deepgram, openai, silero

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

class OpenAITTSAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice. You're helping me test ... yourself ... since you're the AI agent.
                Don't use any unpronouncable characters.
            """,
            stt="assemblyai/universal-streaming",
            llm="openai/gpt-4.1-mini",
            tts="cartesia/sonic-2:6f84f4b8-58a2-430c-8c79-688dad597532",
            vad=silero.VAD.load()
        )

    async def on_enter(self):
        await self.session.say(f"Hi there! Is there anything I can help you with?")

async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=OpenAITTSAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))