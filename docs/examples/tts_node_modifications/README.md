---
title: TTS Node Override
category: pipeline-tts
tags: [pipeline-tts, deepgram, openai, rime]
difficulty: intermediate
description: Shows how to override the default TTS node to do replacements on the output.
demonstrates:
  - Using the `tts_node` method to override the default TTS node and add custom logic to do replacements on the output, like replacing "lol" with "<laughs>".
---

This example overrides `tts_node` to intercept LLM output before it reaches TTS. The agent swaps casual "lol" responses with a `<laugh>` tag so the TTS voice reads them differently.

## Prerequisites

- Add a `.env` in this directory with your LiveKit credentials:
  ```
  LIVEKIT_URL=your_livekit_url
  LIVEKIT_API_KEY=your_api_key
  LIVEKIT_API_SECRET=your_api_secret
  DEEPGRAM_API_KEY=your_deepgram_key
  OPENAI_API_KEY=your_openai_key
  RIME_API_KEY=your_rime_key
  ```
- Install dependencies:
  ```bash
  pip install "livekit-agents[silero]" python-dotenv livekit-plugins-deepgram livekit-plugins-openai livekit-plugins-rime
  ```

## Load configuration and create the AgentServer

Load your environment variables and set up logging to see the before/after replacements. Create an AgentServer to manage sessions.

```python
import logging
from typing import AsyncIterable
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession, ModelSettings
from livekit.plugins import deepgram, openai, silero, rime

load_dotenv()

logger = logging.getLogger("tts_node")
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

## Define the agent and override tts_node

Use Deepgram STT, GPT-4o, and Rime TTS. Override `tts_node` to wrap the outgoing text stream and modify it before synthesis.

```python
class TtsNodeOverrideAgent(Agent):
    def __init__(self, vad) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice.
                Feel free to use "lol" in your responses when something is funny.
            """,
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o"),
            tts=rime.TTS(model="arcana"),
            vad=vad
        )

    async def tts_node(self, text: AsyncIterable[str], model_settings: ModelSettings):
        """Modify the TTS output by replacing 'lol' with '<laugh>'."""
```

## Replace text chunks before synthesis

Iterate over the async text stream, replace "lol"/"LOL", log the swap, and delegate to the default TTS node with the modified stream.

```python
        async def process_text():
            async for chunk in text:
                original_chunk = chunk
                modified_chunk = chunk.replace("lol", "<laugh>").replace("LOL", "<laugh>")

                if original_chunk != modified_chunk:
                    logger.info(f"TTS original: '{original_chunk}'")
                    logger.info(f"TTS modified: '{modified_chunk}'")

                yield modified_chunk

        return Agent.default.tts_node(self, process_text(), model_settings)
```

## Greet on entry

Send a short greeting so you can immediately hear the behavior when you respond with something funny.

```python
    async def on_enter(self):
        await self.session.say("Hi there! Is there anything I can help you with? If you say something funny, I might respond with lol.")
```

## Create the RTC session entrypoint

Start the agent in your LiveKit room; any "lol" in responses will be replaced before TTS renders audio.

```python
@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession()

    await session.start(
        agent=TtsNodeOverrideAgent(vad=ctx.proc.userdata["vad"]),
        room=ctx.room
    )
    await ctx.connect()
```

## Run it

```console
python tts_node_modifications.py console
```

## How it works

1. `tts_node` lets you intercept the text stream headed to TTS.
2. A wrapper coroutine replaces target phrases and logs the changes.
3. The modified stream is passed to the default TTS pipeline so timing/buffering are preserved.
4. Rime TTS renders the adjusted text to audio.

## Full example

```python
import logging
from typing import AsyncIterable
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession, ModelSettings
from livekit.plugins import deepgram, openai, silero, rime

load_dotenv()

logger = logging.getLogger("tts_node")
logger.setLevel(logging.INFO)

class TtsNodeOverrideAgent(Agent):
    def __init__(self, vad) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice.
                Feel free to use "lol" in your responses when something is funny.
            """,
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o"),
            tts=rime.TTS(model="arcana"),
            vad=vad
        )

    async def tts_node(self, text: AsyncIterable[str], model_settings: ModelSettings):
        """Modify the TTS output by replacing 'lol' with '<laugh>'."""

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

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession()

    await session.start(
        agent=TtsNodeOverrideAgent(vad=ctx.proc.userdata["vad"]),
        room=ctx.room
    )
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
```
