"""
---
title: LLM-Powered Content Filter
category: pipeline-llm
tags: [content_moderation, deepgram, openai, cartesia]
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
import asyncio
from typing import Optional, Any
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, inference, AgentServer, cli
from livekit.plugins import openai, silero
from livekit.agents.llm import ChatContext, ChatMessage

load_dotenv()

logger = logging.getLogger("complex-content-filter")
logger.setLevel(logging.INFO)

class ContentFilterAgent(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="You are a helpful agent.")
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

            async with self.session.llm.chat(chat_ctx=chat_ctx, tools=tools, tool_choice=None) as stream:
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

                                    for buffered_chunk in chunk_buffer:
                                        yield buffered_chunk
                                    chunk_buffer = []

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
    agent = ContentFilterAgent()

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
