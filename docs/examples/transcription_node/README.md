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

This example overrides `transcription_node` to intercept STT text, replace words, and inject emojis before the LLM sees the transcript. The agent streams chunks asynchronously so replacements happen mid-utterance.

## Prerequisites

- Add a `.env` in this directory with your LiveKit credentials:
  ```
  LIVEKIT_URL=your_livekit_url
  LIVEKIT_API_KEY=your_api_key
  LIVEKIT_API_SECRET=your_api_secret
  ```
- Install dependencies:
  ```bash
  pip install "livekit-agents[silero]" python-dotenv
  ```

## Load configuration and create the AgentServer

Import dotenv and set up logging to watch the replacements happening. Create an AgentServer to manage sessions.

```python
import logging
from typing import AsyncIterable
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession, inference, ModelSettings
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("transcription-node")
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

## Define the agent and override transcription_node

Create a lightweight Agent with just instructions. Override `transcription_node` to wrap the incoming text stream and swap words on the fly.

```python
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
        replacements = {"hello": "👋 HELLO", "goodbye": "GOODBYE 👋"}
```

## Stream and modify text chunks

Walk the async text stream, perform replacements, log changes, and yield the modified chunks back to the pipeline. The LLM receives the tweaked transcript in real time.

```python
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
```

## Create the RTC session entrypoint

Create an AgentSession with STT/LLM/TTS/VAD configured, start the session with the agent, and connect to the room.

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

    await session.start(agent=TranscriptionModifierAgent(), room=ctx.room)
    await ctx.connect()
```

## Run it

```console
python transcription_node.py console
```

## How it works

1. Deepgram STT streams transcription chunks via the inference gateway.
2. `transcription_node` wraps the chunk stream and replaces target words with emoji-decorated versions.
3. The modified text flows downstream to the LLM and TTS.
4. Logging shows each replacement so you can verify mid-stream edits.

## Full example

```python
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
```
