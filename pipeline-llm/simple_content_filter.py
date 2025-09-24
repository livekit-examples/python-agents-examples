"""
---
title: Simple Content Filter
category: pipeline-llm
tags: [keyword_filtering, offensive_terms, inline_replacement]
difficulty: beginner
description: Basic keyword-based content filter with inline replacement
demonstrates:
  - Simple keyword filtering approach
  - Inline content replacement
  - Custom llm_node override
  - Static offensive terms list
  - Stream processing with substitution
---
"""

import logging
from pathlib import Path
from typing import AsyncIterable, Optional
from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import openai, deepgram, silero
import asyncio

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

logger = logging.getLogger("simple-content-filter")
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
    
    async def llm_node(
        self, chat_ctx, tools, model_settings=None
    ):
        async def process_stream():
            async with self.llm.chat(chat_ctx=chat_ctx, tools=tools, tool_choice=None) as stream:
                async for chunk in stream:
                    if chunk is None:
                        continue
                        
                    content = getattr(chunk.delta, 'content', None) if hasattr(chunk, 'delta') else str(chunk)
                    if content is None:
                        yield chunk
                        continue
                        
                    offensive_terms = ['fail']
                    print(content)
                    yield "CONTENT FILTERED" if any(term in content.lower() for term in offensive_terms) else chunk

        return process_stream()

async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=SimpleAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))