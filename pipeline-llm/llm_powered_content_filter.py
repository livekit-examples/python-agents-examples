"""
---
title: LLM-Powered Content Filter
category: pipeline-llm
tags: [content_moderation, dual_llm, sentence_buffering, stream_processing]
difficulty: advanced
description: Content filter using a separate LLM for real-time moderation decisions
demonstrates:
  - Dual LLM setup (main + moderator)
  - Sentence-level content buffering
  - Stream processing with moderation checks
  - Custom llm_node override for filtering
  - Handling different chunk formats
  - Real-time content evaluation
---
"""

import logging
from pathlib import Path
from typing import Optional, Any
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import openai, deepgram, silero
from livekit.agents.llm import ChatContext, ChatMessage
import asyncio

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

logger = logging.getLogger("complex-content-filter")
logger.setLevel(logging.INFO)

class SimpleAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="You are a helpful agent.",
            stt=deepgram.STT(),
            llm=openai.LLM(),
            tts=openai.TTS(),
            vad=silero.VAD.load()
        )
        self.moderator_llm = openai.LLM(model="gpt-4o-mini")
    
    async def evaluate_content(self, text: str) -> bool:
        """Evaluate if content is appropriate using a separate LLM."""
        moderation_ctx = ChatContext([
            ChatMessage(
                type="message",
                role="system",
                content=["You are a content moderator. Respond ONLY with 'APPROPRIATE' or 'INAPPROPRIATE'. Respond with 'INAPPROPRIATE' if the text mentions strawberries."]
            ),
            ChatMessage(type="message", role="user", content=[f"Evaluate: {text}"])
        ])
        
        response = ""
        async with self.moderator_llm.chat(chat_ctx=moderation_ctx) as stream:
            async for chunk in stream:
                if not chunk:
                    continue
                content = getattr(chunk.delta, 'content', None) if hasattr(chunk, 'delta') else str(chunk)
                if content:
                    response += content
        
        response = response.strip().upper()
        logger.info(f"Moderation response for '{text}': {response}")
        return "INAPPROPRIATE" not in response
    
    async def on_enter(self):
        self.session.generate_reply()
    
    def _extract_content(self, chunk: Any) -> Optional[str]:
        """Extract content from a chunk, handling different chunk formats."""
        if not chunk:
            return None
        if isinstance(chunk, str):
            return chunk
        if hasattr(chunk, 'delta'):
            return getattr(chunk.delta, 'content', None)
        return None
    
    async def llm_node(self, chat_ctx, tools, model_settings=None):
        async def process_stream():
            buffer = ""
            chunk_buffer = []
            sentence_end_chars = {'.', '!', '?'}
            
            async with self.llm.chat(chat_ctx=chat_ctx, tools=tools, tool_choice=None) as stream:
                try:
                    async for chunk in stream:
                        content = self._extract_content(chunk)
                        chunk_buffer.append(chunk)
                        
                        if content:
                            buffer += content
                            
                            if any(char in buffer for char in sentence_end_chars):
                                last_end = max(buffer.rfind(char) for char in sentence_end_chars if char in buffer)
                                if last_end != -1:
                                    sentence = buffer[:last_end + 1]
                                    buffer = buffer[last_end + 1:]
                                    
                                    if not await self.evaluate_content(sentence):
                                        yield "Content filtered."
                                        return
                                    
                                    # Yield buffered chunks if content is appropriate
                                    for buffered_chunk in chunk_buffer:
                                        yield buffered_chunk
                                    chunk_buffer = []
                    
                    # Check any remaining complete sentence
                    if buffer and any(buffer.endswith(char) for char in sentence_end_chars):
                        if not await self.evaluate_content(buffer):
                            yield "Content filtered."
                            return
                        for buffered_chunk in chunk_buffer:
                            yield buffered_chunk
                            
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    logger.error(f"Error in content filtering: {str(e)}")
                    yield "[Error in content filtering]"

        return process_stream()

async def entrypoint(ctx: JobContext):
    await AgentSession().start(agent=SimpleAgent(), room=ctx.room)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))