"""
---
title: Short Replies Only
category: pipeline-tts
tags: [pipeline-tts, openai, deepgram]
difficulty: beginner
description: Shows how to override the default TTS node to only respond with short replies based on the number of chunks.
demonstrates:
  - Using the `tts_node` method to override the default TTS node and add custom logic to only respond with short replies.
  - Using the `session.interrupt` method to interrupt the agent if it's taking too long to respond, and then informing the user with `session.say`
---
"""
from pathlib import Path
from typing import AsyncIterable
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, ModelSettings
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import deepgram, openai, silero, rime

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

logger = logging.getLogger("tts_node")
logger.setLevel(logging.INFO)

class ShortRepliesOnlyAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice.
            """,
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o"),
            tts=rime.TTS(model="arcana"),
            vad=silero.VAD.load()
        )
    
    async def tts_node(self, text: AsyncIterable[str], model_settings: ModelSettings):
        MAX_CHUNKS = 20
        chunk_count = 0

        async def process_text():
            nonlocal chunk_count
            interrupted = False
            async for chunk in text:
                chunk_count += 1
                if chunk_count > MAX_CHUNKS and not interrupted:
                    logger.info(f"tts_node: Exceeded {MAX_CHUNKS} chunks. Interrupting.")
                    self.session.interrupt()
                    self.session.say("I'm sorry, that will take too long to say.")
                    interrupted = True
                    break

                if not interrupted:
                    yield chunk

        return Agent.default.tts_node(self, process_text(), model_settings)

    async def on_enter(self):
        await self.session.say(f"Hi there! Is there anything I can help you with?")

async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=ShortRepliesOnlyAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))