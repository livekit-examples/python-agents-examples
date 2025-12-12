---
title: Pipeline Translator Agent
category: translation
tags: [translation, multilingual, french, elevenlabs, deepgram, openai]
difficulty: intermediate
description: Simple translation pipeline that converts English speech to French
demonstrates:
  - Direct language translation workflow
  - Multilingual TTS configuration with ElevenLabs
  - Simple translation-focused agent instructions
  - Clean input-to-output translation pipeline
  - Voice-to-voice translation system
---

This example shows how to build a simple voice-to-voice translator: listen in English, translate with an LLM, and speak the result in French with ElevenLabs TTS. Instead of using LiveKit Inference, this example uses agent plugins to connect directly to OpenAI and ElevenLabs.

## Prerequisites

- Add a `.env` in this directory with your credentials:
  ```
  LIVEKIT_URL=your_livekit_url
  LIVEKIT_API_KEY=your_api_key
  LIVEKIT_API_SECRET=your_api_secret
  OPENAI_API_KEY=your_api_key
  ELEVENLABS_API_KEY=your_api_key
  DEEPGRAM_API_KEY=your_api_key
  ```
- Install dependencies:
  ```bash
  pip install "livekit-agents[silero,openai,elevenlabs,deepgram]" python-dotenv
  ```

<!-- {% step %} -->
<!-- {% instructions %} -->
## Load environment, logging, and define an AgentServer

Load your `.env` and set up logging to trace translation events.
<!-- {% /instructions %} -->

<!-- {% stepCode %} -->
```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession
from livekit.plugins import openai, silero, deepgram, elevenlabs

load_dotenv()

logger = logging.getLogger("pipeline-translator")
logger.setLevel(logging.INFO)

server = AgentServer()
```
<!-- {% /stepCode %} -->
<!-- {% /step %}-->

<!-- {% step %} -->
<!-- {% instructions %} -->
## Define the translation agent

Keep the agent lightweight with focused instructions: always translate from English to French and respond only with the translation.
<!-- {% /instructions %} -->

<!-- {% stepCode %} -->
```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession
from livekit.plugins import openai, silero, deepgram, elevenlabs

load_dotenv()

logger = logging.getLogger("pipeline-translator")
logger.setLevel(logging.INFO)

server = AgentServer()
```
<!-- {% added %} -->
```python
class TranslatorAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a translator. You translate the user's speech from English to French.
                Every message you receive, translate it directly into French.
                Do not respond with anything else but the translation.
            """
        )

    async def on_enter(self):
        self.session.generate_reply()
```
<!-- {% /added %} -->
<!-- {% /stepCode %} -->
<!-- {% /step %}-->

<!-- {% step %} -->
<!-- {% instructions %} -->
## Prewarm VAD for faster connections

Preload the VAD model once per process to reduce connection latency.
<!-- {% /instructions %} -->

<!-- {% stepCode %} -->
```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession
from livekit.plugins import openai, silero, deepgram, elevenlabs

load_dotenv()

logger = logging.getLogger("pipeline-translator")
logger.setLevel(logging.INFO)

server = AgentServer()


class TranslatorAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a translator. You translate the user's speech from English to French.
                Every message you receive, translate it directly into French.
                Do not respond with anything else but the translation.
            """
        )

    async def on_enter(self):
        self.session.generate_reply()
```
<!-- {% added %} -->
```python
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm
```
<!-- {% /added %} -->
<!-- {% /stepCode %} -->
<!-- {% /step %}-->

<!-- {% step %} -->
<!-- {% instructions %} -->
## Define the rtc session with translation pipeline

Create the session with Deepgram STT, OpenAI LLM, and ElevenLabs multilingual TTS for French output.
<!-- {% /instructions %} -->

<!-- {% stepCode %} -->
```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession
from livekit.plugins import openai, silero, deepgram, elevenlabs

load_dotenv()

logger = logging.getLogger("pipeline-translator")
logger.setLevel(logging.INFO)

server = AgentServer()


class TranslatorAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a translator. You translate the user's speech from English to French.
                Every message you receive, translate it directly into French.
                Do not respond with anything else but the translation.
            """
        )

    async def on_enter(self):
        self.session.generate_reply()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm
```
<!-- {% added %} -->
```python
@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=deepgram.STT(),
        llm=openai.LLM(),
        tts=elevenlabs.TTS(model="eleven_multilingual_v2"),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(agent=TranslatorAgent(), room=ctx.room)
    await ctx.connect()
```
<!-- {% /added %} -->
<!-- {% /stepCode %} -->
<!-- {% /step %}-->

<!-- {% step %} -->
<!-- {% instructions %} -->
## Run the server

Start the agent server with the CLI runner.
<!-- {% /instructions %} -->

<!-- {% stepCode %} -->
```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession
from livekit.plugins import openai, silero, deepgram, elevenlabs

load_dotenv()

logger = logging.getLogger("pipeline-translator")
logger.setLevel(logging.INFO)

server = AgentServer()


class TranslatorAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a translator. You translate the user's speech from English to French.
                Every message you receive, translate it directly into French.
                Do not respond with anything else but the translation.
            """
        )

    async def on_enter(self):
        self.session.generate_reply()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=deepgram.STT(),
        llm=openai.LLM(),
        tts=elevenlabs.TTS(model="eleven_multilingual_v2"),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(agent=TranslatorAgent(), room=ctx.room)
    await ctx.connect()
```
<!-- {% added %} -->
```python
if __name__ == "__main__":
    cli.run_app(server)
```
<!-- {% /added %} -->
<!-- {% /stepCode %} -->
<!-- {% /step %}-->

## Run it

```bash
python pipeline_translator.py console
```

## How it works

1. Deepgram handles English speech-to-text transcription.
2. OpenAI generates a French translation from the transcript.
3. ElevenLabs multilingual TTS speaks the translated text in French.
4. Silero VAD controls turn-taking between user and agent.
5. The agent triggers an initial response on entry so the user hears French output immediately.

## Full example

```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession
from livekit.plugins import openai, silero, deepgram, elevenlabs

load_dotenv()

logger = logging.getLogger("pipeline-translator")
logger.setLevel(logging.INFO)

class TranslatorAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a translator. You translate the user's speech from English to French.
                Every message you receive, translate it directly into French.
                Do not respond with anything else but the translation.
            """
        )

    async def on_enter(self):
        self.session.generate_reply()

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=deepgram.STT(),
        llm=openai.LLM(),
        tts=elevenlabs.TTS(model="eleven_multilingual_v2"),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(agent=TranslatorAgent(), room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
```
