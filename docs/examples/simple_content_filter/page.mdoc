---
title: Simple Content Filter
category: pipeline-llm
tags: [pipeline-llm, openai, deepgram]
difficulty: beginner
description: Basic keyword-based content filter with inline replacement
demonstrates:
  - Simple keyword filtering approach
  - Inline content replacement
  - Custom llm_node override
  - Static offensive terms list
  - Stream processing with substitution
---

This example demonstrates how to implement a basic content filter by overriding the `llm_node` method. The filter scans the LLM's streaming output for specific keywords and replaces matching chunks with a filtered message. This is a simple approach to content moderation in voice agents.

## Prerequisites

- Add a `.env` in this directory with your LiveKit credentials:
  ```
  LIVEKIT_URL=your_livekit_url
  LIVEKIT_API_KEY=your_api_key
  LIVEKIT_API_SECRET=your_api_secret
  ```
- Install dependencies:
  ```bash
  pip install "livekit-agents[silero,deepgram,openai]" python-dotenv
  ```

## Set up logging and create the AgentServer

Load environment variables and configure logging. Create an AgentServer to manage the agent lifecycle.

```python
import logging
from dotenv import load_dotenv
from livekit.agents import AgentServer, AgentSession, JobContext, JobProcess, cli, Agent, inference
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("simple-content-filter")
logger.setLevel(logging.INFO)

server = AgentServer()
```

## Prewarm VAD for faster connections

Preload the VAD model once per process. This runs before any sessions start and stores the VAD instance in `proc.userdata` so it can be reused, cutting down on connection latency.

```python
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm
```

## Define the agent with a custom LLM node

Keep the Agent lightweight with just instructions. The custom `llm_node` override processes the streaming LLM output and checks each chunk for offensive terms, replacing matches with a filtered message.

```python
class SimpleAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent.
            """,
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
```

## Define the RTC session entrypoint

Create the AgentSession with STT, LLM, TTS, and VAD configured. The models are defined here in the session rather than in the agent, keeping the agent lightweight.

```python
@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3", language="en"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        stt=inference.STT(model="deepgram/nova-3", language="en"),
        llm=inference.LLM(model="openai/gpt-5-mini"),
        tts=inference.TTS(
            model="cartesia/sonic-3", 
            voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"
        ),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )
    agent = SimpleAgent()

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()
```

## Run the server

The `cli.run_app()` function starts the agent server, manages the worker lifecycle, and processes incoming jobs.

```python
if __name__ == "__main__":
    cli.run_app(server)
```

## Run it

Run the agent using the `console` command for local testing with a mocked room:

```bash
python simple_content_filter.py console
```

To test with a real LiveKit room, use dev mode:

```bash
python simple_content_filter.py dev
```

## How it works

1. When the user speaks, their audio is transcribed and sent to the LLM.
2. The custom `llm_node` intercepts the LLM's streaming response.
3. Each chunk is checked against a list of offensive terms (in this case, just "fail").
4. If a term is found, the chunk is replaced with "CONTENT FILTERED".
5. Clean chunks pass through unchanged to the TTS for speech synthesis.

## Full example

```python
import logging
from dotenv import load_dotenv
from livekit.agents import AgentServer, AgentSession, JobContext, JobProcess, cli, Agent, inference
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("simple-content-filter")
logger.setLevel(logging.INFO)

class SimpleAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent.
            """,
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

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3", language="en"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        stt=inference.STT(model="deepgram/nova-3", language="en"),
        llm=inference.LLM(model="openai/gpt-5-mini"),
        tts=inference.TTS(
            model="cartesia/sonic-3", 
            voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"
        ),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )
    agent = SimpleAgent()

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
```
