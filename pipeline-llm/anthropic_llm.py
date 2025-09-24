"""
---
title: Anthropic LLM
category: pipeline-llm
tags: [pipeline-llm, openai, deepgram]
difficulty: intermediate
description: Shows how to use the Anthropic LLM.
demonstrates:
  - Using the Anthropic LLM.
---
"""
import logging
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import anthropic, openai, silero, deepgram

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

logger = logging.getLogger("anthropic_llm")
logger.setLevel(logging.INFO)

class SimpleAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent.
            """,
            stt=deepgram.STT(),
            llm=anthropic.LLM(model="claude-3-5-sonnet-20240620"),
            tts=openai.TTS(instructions="You are a helpful assistant with a pleasant voice. Speak in a natural, conversational tone."),
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