"""
---
title: Only Greet
category: pipeline-tts
tags: [pipeline-tts, openai, deepgram]
difficulty: beginner
description: Greets the user when they join the room, but doesn't respond to anything else.
demonstrates:
  - This agent only has TTS, so it can only speak, not listen or think.
---
"""

from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import openai

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

class GreeterAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="You are a simple greeter that welcomes users when they join.",
            tts=openai.TTS()
        )
    
    async def on_enter(self):
        self.session.say("Hi there! Is there anything I can help you with?")

async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=GreeterAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))