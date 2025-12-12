"""
---
title: Transcription Node Modifier
category: pipeline-llm
tags: [transcription_modification, word_replacement, emoji_injection, deepgram, openai, cartesia]
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
from typing import AsyncIterable
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession, inference, ModelSettings
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("transcription-node")
logger.setLevel(logging.INFO)

class TranscriptionModifierAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent.
            """
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

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(agent=TranscriptionModifierAgent(), room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
