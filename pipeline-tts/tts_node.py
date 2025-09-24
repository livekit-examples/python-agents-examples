"""
---
title: TTS Node Override
category: pipeline-tts
tags: [pipeline-tts, openai, deepgram]
difficulty: intermediate
description: Shows how to override the default TTS node to do replacements on the output.
demonstrates:
  - Using the `tts_node` method to override the default TTS node and add custom logic to do replacements on the output, like replacing "lol" with "<laughs>".
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

class TtsNodeOverrideAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice.
                Feel free to use "lol" in your responses when something is funny.
            """,
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o"),
            tts=rime.TTS(model="arcana"),
            vad=silero.VAD.load()
        )
    
    async def tts_node(self, text: AsyncIterable[str], model_settings: ModelSettings):
        """Modify the TTS output by replacing 'lol' with '<laughs>'."""

        async def process_text():
            async for chunk in text:
                original_chunk = chunk
                modified_chunk = chunk.replace("lol", "<laugh>").replace("LOL", "<laugh>")

                if original_chunk != modified_chunk:
                    logger.info(f"TTS original: '{original_chunk}'")
                    logger.info(f"TTS modified: '{modified_chunk}'")

                yield modified_chunk

        return Agent.default.tts_node(self, process_text(), model_settings)

    async def on_enter(self):
        await self.session.say(f"Hi there! Is there anything I can help you with? If you say something funny, I might respond with lol.")

async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=TtsNodeOverrideAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))