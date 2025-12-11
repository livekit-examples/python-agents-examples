---
title: TTS Comparison
category: pipeline-tts
tags: [pipeline-tts, deepgram, openai, rime, elevenlabs, cartesia, playai]
difficulty: intermediate
description: Switches between different TTS providers using function tools.
demonstrates:
  - Using function tools to switch between different TTS providers.
  - Each function tool returns a new agent with the same instructions, but with a different TTS provider.
---

This example demonstrates a voice assistant that allows real-time switching between different Text-to-Speech providers to compare voice quality, latency, and characteristics. Each provider has its own agent class, and function tools allow seamless switching mid-conversation.

## Prerequisites

- Add a `.env` in this directory with your LiveKit credentials and API keys for each TTS provider:
  ```
  LIVEKIT_URL=your_livekit_url
  LIVEKIT_API_KEY=your_api_key
  LIVEKIT_API_SECRET=your_api_secret
  OPENAI_API_KEY=your_openai_key
  DEEPGRAM_API_KEY=your_deepgram_key
  RIME_API_KEY=your_rime_key
  ELEVENLABS_API_KEY=your_elevenlabs_key
  CARTESIA_API_KEY=your_cartesia_key
  PLAYAI_API_KEY=your_playai_key
  ```
- Install dependencies:
  ```bash
  pip install "livekit-agents[silero,deepgram,openai,rime,elevenlabs,playai,cartesia]" python-dotenv
  ```

## Load environment and create the AgentServer

Import the necessary modules, load environment variables, and create an AgentServer. The VAD is prewarmed once per process and shared across all agents.

```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession, function_tool
from livekit.plugins import deepgram, openai, rime, elevenlabs, cartesia, playai, silero

logger = logging.getLogger("tts-comparison")
logger.setLevel(logging.INFO)

load_dotenv()

server = AgentServer()
```

## Prewarm VAD for faster connections

Preload the VAD model once per process. The VAD instance is passed to each agent so they can reuse it when switching providers.

```python
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm
```

## Define agents for each TTS provider

Each agent class configures a different TTS provider while sharing the same STT, LLM, and VAD. Function tools return new agent instances to enable switching. The VAD is stored so it can be passed to the next agent during transfer.

```python
class RimeAgent(Agent):
    def __init__(self, vad) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice.
                You are currently using the Rime TTS provider.
                You can switch to a different TTS provider if asked.
                Don't use any unpronouncable characters.
            """,
            stt=deepgram.STT(),
            llm=openai.LLM(),
            tts=rime.TTS(),
            vad=vad
        )
        self._vad = vad

    async def on_enter(self) -> None:
        await self.session.say("Hello! I'm now using the Rime TTS voice. How does it sound?")

    @function_tool
    async def switch_to_elevenlabs(self):
        """Switch to ElevenLabs TTS voice"""
        return ElevenLabsAgent(self._vad)

    @function_tool
    async def switch_to_cartesia(self):
        """Switch to Cartesia TTS voice"""
        return CartesiaAgent(self._vad)

    @function_tool
    async def switch_to_playai(self):
        """Switch to PlayAI TTS voice"""
        return PlayAIAgent(self._vad)
```

## Additional TTS provider agents

The ElevenLabs, Cartesia, and PlayAI agents follow the same pattern—each configures its own TTS provider and provides function tools to switch to the other providers.

```python
class ElevenLabsAgent(Agent):
    def __init__(self, vad) -> None:
        super().__init__(
            instructions="...",
            stt=deepgram.STT(),
            llm=openai.LLM(),
            tts=elevenlabs.TTS(),
            vad=vad
        )
        self._vad = vad

    # ... on_enter and switch functions
```

## Create the RTC session entrypoint

Start with the Rime agent and pass the prewarmed VAD. The session handles agent transfers automatically when function tools return new agents.

```python
@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession()

    await session.start(
        agent=RimeAgent(vad=ctx.proc.userdata["vad"]),
        room=ctx.room
    )
    await ctx.connect()
```

## Run it

```console
python tts_comparison.py dev
```

Try these commands to switch between providers:
- "Switch to ElevenLabs"
- "Use the Cartesia voice"
- "Let me hear PlayAI"
- "Go back to Rime"

## How it works

1. Session starts with the Rime TTS provider.
2. Agent introduces itself using the current voice.
3. User can request to switch providers (e.g., "Switch to ElevenLabs").
4. Function tool returns a new agent instance with the requested TTS.
5. Session transfers to the new agent and `on_enter()` provides audio confirmation.
6. The prewarmed VAD is passed to each new agent during transfer.

## Full example

```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession, function_tool
from livekit.plugins import deepgram, openai, rime, elevenlabs, cartesia, playai, silero

logger = logging.getLogger("tts-comparison")
logger.setLevel(logging.INFO)

load_dotenv()

class RimeAgent(Agent):
    def __init__(self, vad) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice.
                You are currently using the Rime TTS provider.
                You can switch to a different TTS provider if asked.
                Don't use any unpronouncable characters.
            """,
            stt=deepgram.STT(),
            llm=openai.LLM(),
            tts=rime.TTS(),
            vad=vad
        )
        self._vad = vad

    async def on_enter(self) -> None:
        await self.session.say("Hello! I'm now using the Rime TTS voice. How does it sound?")

    @function_tool
    async def switch_to_elevenlabs(self):
        """Switch to ElevenLabs TTS voice"""
        return ElevenLabsAgent(self._vad)

    @function_tool
    async def switch_to_cartesia(self):
        """Switch to Cartesia TTS voice"""
        return CartesiaAgent(self._vad)

    @function_tool
    async def switch_to_playai(self):
        """Switch to PlayAI TTS voice"""
        return PlayAIAgent(self._vad)


class ElevenLabsAgent(Agent):
    def __init__(self, vad) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice.
                You are currently using the ElevenLabs TTS provider.
                You can switch to a different TTS provider if asked.
                Don't use any unpronouncable characters.
            """,
            stt=deepgram.STT(),
            llm=openai.LLM(),
            tts=elevenlabs.TTS(),
            vad=vad
        )
        self._vad = vad

    async def on_enter(self) -> None:
        await self.session.say("Hello! I'm now using the ElevenLabs TTS voice. What do you think of how I sound?")

    @function_tool
    async def switch_to_rime(self):
        """Switch to Rime TTS voice"""
        return RimeAgent(self._vad)

    @function_tool
    async def switch_to_cartesia(self):
        """Switch to Cartesia TTS voice"""
        return CartesiaAgent(self._vad)

    @function_tool
    async def switch_to_playai(self):
        """Switch to PlayAI TTS voice"""
        return PlayAIAgent(self._vad)


class CartesiaAgent(Agent):
    def __init__(self, vad) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice.
                You are currently using the Cartesia TTS provider.
                You can switch to a different TTS provider if asked.
                Don't use any unpronouncable characters.
            """,
            stt=deepgram.STT(),
            llm=openai.LLM(),
            tts=cartesia.TTS(),
            vad=vad
        )
        self._vad = vad

    async def on_enter(self) -> None:
        await self.session.say("Hello! I'm now using the Cartesia TTS voice. How do I sound to you?")

    @function_tool
    async def switch_to_rime(self):
        """Switch to Rime TTS voice"""
        return RimeAgent(self._vad)

    @function_tool
    async def switch_to_elevenlabs(self):
        """Switch to ElevenLabs TTS voice"""
        return ElevenLabsAgent(self._vad)

    @function_tool
    async def switch_to_playai(self):
        """Switch to PlayAI TTS voice"""
        return PlayAIAgent(self._vad)


class PlayAIAgent(Agent):
    def __init__(self, vad) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice.
                You are currently using the PlayAI TTS provider.
                You can switch to a different TTS provider if asked.
                Don't use any unpronouncable characters.
            """,
            stt=deepgram.STT(),
            llm=openai.LLM(),
            tts=playai.TTS(),
            vad=vad
        )
        self._vad = vad

    async def on_enter(self) -> None:
        await self.session.say("Hello! I'm now using the PlayAI TTS voice. What are your thoughts on how I sound?")

    @function_tool
    async def switch_to_rime(self):
        """Switch to Rime TTS voice"""
        return RimeAgent(self._vad)

    @function_tool
    async def switch_to_elevenlabs(self):
        """Switch to ElevenLabs TTS voice"""
        return ElevenLabsAgent(self._vad)

    @function_tool
    async def switch_to_cartesia(self):
        """Switch to Cartesia TTS voice"""
        return CartesiaAgent(self._vad)


server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession()

    await session.start(
        agent=RimeAgent(vad=ctx.proc.userdata["vad"]),
        room=ctx.room
    )
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
```
