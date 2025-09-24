"""
---
title: Transcription Node Modifier
category: pipeline-llm
tags: [transcription_modification, word_replacement, emoji_injection]
difficulty: intermediate
description: Modifies transcriptions by replacing words with custom versions
demonstrates:
  - Custom transcription_node override
  - Word replacement in transcriptions
  - Emoji injection in text
  - Async stream processing for text
  - Model settings usage
---
"""

import logging
from pathlib import Path
from typing import AsyncIterable
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, ModelSettings
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import openai, deepgram, silero

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

logger = logging.getLogger("openai_llm")
logger.setLevel(logging.INFO)

class SimpleAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent.
            """,
            stt=deepgram.STT(),
            llm=openai.LLM(),
            tts=openai.TTS(),
            vad=silero.VAD.load()
        )
    
    async def on_enter(self):
        self.session.generate_reply()

    async def transcription_node(self, text: AsyncIterable[str], model_settings: ModelSettings):
        """Modify the transcription output by replacing certain words."""
        replacements = {
            "hello": "👋 HELLO",
            "goodbye": "GOODBYE 👋",
        }

        async def process_text():
            async for chunk in text:
                modified_chunk = chunk
                original_chunk = chunk

                for word, replacement in replacements.items():
                    if word in modified_chunk.lower() or word.capitalize() in modified_chunk:
                        logger.info(f"Replacing '{word}' with '{replacement}' in transcript")

                    modified_chunk = modified_chunk.replace(word, replacement)
                    modified_chunk = modified_chunk.replace(word.capitalize(), replacement)

                if original_chunk != modified_chunk:
                    logger.info(f"Original: '{original_chunk}'")
                    logger.info(f"Modified: '{modified_chunk}'")

                yield modified_chunk

        return process_text()

async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=SimpleAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))