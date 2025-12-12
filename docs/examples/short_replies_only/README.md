---
title: Short Replies Only
category: pipeline-tts
tags: [pipeline-tts, openai, deepgram, rime]
difficulty: beginner
description: Shows how to override the default TTS node to only respond with short replies based on the number of chunks.
demonstrates:
  - Using the `tts_node` method to override the default TTS node and add custom logic to only respond with short replies.
  - Using the `session.interrupt` method to interrupt the agent if it's taking too long to respond, and then informing the user with `session.say`
---

This example shows how to override the default TTS node to limit response length. When the LLM generates a response that's too long (more than 20 text chunks), the agent interrupts itself and apologizes rather than droning on. This is useful for voice interfaces where brevity matters.

## Prerequisites

- Add a `.env` in this directory with your LiveKit credentials:
  ```
  LIVEKIT_URL=your_livekit_url
  LIVEKIT_API_KEY=your_api_key
  LIVEKIT_API_SECRET=your_api_secret
  ```
- Install dependencies:
  ```bash
  pip install "livekit-agents[silero,deepgram,rime]" python-dotenv
  ```

## Set up logging and create the AgentServer

Load environment variables and configure logging for debugging. Then create an AgentServer which manages the lifecycle of your agent sessions.

```python
from typing import AsyncIterable
import logging
from dotenv import load_dotenv
from livekit.agents import AgentServer, AgentSession, JobContext, JobProcess, cli, Agent, inference, ModelSettings
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("tts_node")
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

## Define the agent with a custom TTS node

Keep your Agent lightweight with just instructions and the custom `tts_node` override. The `tts_node` method processes the streaming text from the LLM and counts chunks. If it exceeds the limit, it interrupts the response and informs the user.

```python
class ShortRepliesOnlyAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice.
            """,
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
        await self.session.say("Hi there! Is there anything I can help you with?")
```

## Define the RTC session entrypoint

Create the AgentSession with STT, LLM, TTS, and VAD configured. Then start the session and connect to the room. The models are defined here in the session rather than in the agent, keeping the agent lightweight.

```python
@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3", language="en"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(model="rime/arcana"),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )
    agent = ShortRepliesOnlyAgent()

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()
```

## Run the server

The `cli.run_app()` function starts the agent server. It manages the worker lifecycle, connects to LiveKit, and processes incoming jobs.

```python
if __name__ == "__main__":
    cli.run_app(server)
```

## Run it

Run the agent using the `console` command, which starts the agent in console mode. This mode is useful for testing and debugging with a mocked LiveKit room.

```bash
python short_replies_only.py console
```

To test with a real room, use dev mode:

```bash
python short_replies_only.py dev
```

## How it works

1. When the agent needs to speak, the LLM generates text and streams it to the TTS node.
2. The custom `tts_node` counts each text chunk as it streams through.
3. If the chunk count exceeds 20, the agent calls `session.interrupt()` to stop the current speech.
4. The agent then says a polite apology message instead of continuing the long response.
5. The `Agent.default.tts_node()` handles the actual text-to-speech conversion for valid chunks.

## Full example

```python
from typing import AsyncIterable
import logging
from dotenv import load_dotenv
from livekit.agents import AgentServer, AgentSession, JobContext, JobProcess, cli, Agent, inference, ModelSettings
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("tts_node")
logger.setLevel(logging.INFO)

class ShortRepliesOnlyAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice.
            """,
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
        await self.session.say("Hi there! Is there anything I can help you with?")

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
        tts=inference.TTS(model="rime/arcana"),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )
    agent = ShortRepliesOnlyAgent()

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
```
