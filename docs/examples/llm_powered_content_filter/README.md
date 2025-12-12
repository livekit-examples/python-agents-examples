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

This example shows how to filter the LLM's output with a second moderation model. The agent buffers sentences from the main LLM stream, checks them with a moderator LLM, and only forwards safe text to the TTS.

## Prerequisites

- Add a `.env` in this directory with your LiveKit credentials:
  ```
  LIVEKIT_URL=your_livekit_url
  LIVEKIT_API_KEY=your_api_key
  LIVEKIT_API_SECRET=your_api_secret
  OPENAI_API_KEY=your_openai_key
  ```
- Install dependencies:
  ```bash
  pip install "livekit-agents[silero]" livekit-plugins-openai python-dotenv
  ```

## Load configuration and logging

Load environment variables and configure logging for monitoring moderation decisions.

```python
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

server = AgentServer()
```

## Prewarm VAD for faster connections

Preload the VAD model once per process to reduce connection latency.

```python
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm
```

## Create the dual-LLM agent

The agent keeps a separate moderator LLM for content checks. The main LLM for responses is provided through the AgentSession using LiveKit inference, while the moderator uses the OpenAI plugin directly for fine-grained control.

```python
class ContentFilterAgent(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="You are a helpful agent.")
        self.moderator_llm = openai.LLM(model="gpt-4o-mini")

    async def on_enter(self):
        self.session.generate_reply()
```

## Evaluate content with a moderator prompt

Send candidate text to the moderator LLM with a strict system prompt that returns only APPROPRIATE/INAPPROPRIATE. Parse the streamed response and return a boolean.

```python
    async def evaluate_content(self, text: str) -> bool:
        moderation_ctx = ChatContext([
            ChatMessage(type="message", role="system", content=["You are a content moderator. Respond ONLY with 'APPROPRIATE' or 'INAPPROPRIATE'. Respond with 'INAPPROPRIATE' if the text mentions strawberries."]),
            ChatMessage(type="message", role="user", content=[f"Evaluate: {text}"])
        ])

        response = ""
        async with self.moderator_llm.chat(chat_ctx=moderation_ctx) as stream:
            async for chunk in stream:
                content = getattr(chunk.delta, "content", None) if hasattr(chunk, "delta") else str(chunk)
                if content:
                    response += content

        return "INAPPROPRIATE" not in response.strip().upper()
```

## Extract content from streamed chunks

This helper normalizes string vs delta-based chunks from the main LLM stream.

```python
    def _extract_content(self, chunk: Any) -> Optional[str]:
        if not chunk:
            return None
        if isinstance(chunk, str):
            return chunk
        if hasattr(chunk, "delta"):
            return getattr(chunk.delta, "content", None)
        return None
```

## Override llm_node to buffer and filter

Buffer text until a sentence-ending punctuation appears. When a sentence completes, send it to the moderator; if approved, yield buffered chunks downstream, otherwise drop them.

```python
    async def llm_node(self, chat_ctx, tools, model_settings=None):
        async def process_stream():
            buffer = ""
            chunk_buffer = []
            sentence_end_chars = {".", "!", "?"}

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
```

## Set up the session

Configure the AgentSession with LiveKit inference for STT, LLM, and TTS. The main LLM is accessed via `self.session.llm` in the `llm_node` override.

```python
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
```

## Run the server

Start the agent server with the CLI.

```python
if __name__ == "__main__":
    cli.run_app(server)
```

## Run it

```console
python llm_powered_content_filter.py console
```

## How it works

1. The main LLM streams responses via LiveKit inference; chunks are buffered until a sentence completes.
2. The moderator LLM (using the OpenAI plugin directly) judges the buffered text; unsafe content is dropped.
3. Safe chunks are replayed to the downstream pipeline (and then to TTS).
4. The agent owns the moderator LLM separately from the session's main LLM.

## Full example

```python
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
        self.moderator_llm = inference.LLM(model="openai/gpt-4.1-mini")

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
```
