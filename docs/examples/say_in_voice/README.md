---
title: Function Tool Voice Switching Agent
category: basics
tags: [tts, voice-switching, function-tools, inworld, deepgram, openai]
difficulty: beginner
description: Demonstrates how to create an agent that can dynamically switch between different voices during a conversation using function tools.
demonstrates:
  - Dynamic TTS voice switching
  - Function tool integration
  - Multiple TTS provider support (Inworld)
---

This example shows how to let an agent switch TTS voices mid-call. A function tool updates the Inworld TTS voice, speaks a phrase, and then restores the default voice.

## Prerequisites

- Add a `.env` in this directory with your LiveKit and Inworld credentials:
  ```
  LIVEKIT_URL=your_livekit_url
  LIVEKIT_API_KEY=your_api_key
  LIVEKIT_API_SECRET=your_api_secret
  INWORLD_API_KEY=your_api_key
  ```
- Install dependencies:
  ```bash
  pip install "livekit-agents[silero,inworld]" python-dotenv
  ```

## Load environment, logging, and define an AgentServer

Load environment variables, initialize logging, and set up the AgentServer.

```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession, inference, function_tool
from livekit.plugins import silero, inworld

load_dotenv()

logger = logging.getLogger("say-in-voice")
logger.setLevel(logging.INFO)

server = AgentServer()
```

## Define the agent with voice switching capability

Create an agent that stores its own TTS instance with Inworld and provides a helper method to temporarily switch voices, speak, then restore the default voice.

```python
class SayPhraseInVoiceAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="You are an agent that can say phrases in different voices."
        )
        self._tts = inworld.TTS(voice="Ashley")

    async def say_phrase_in_voice(self, phrase, voice="Hades"):
        self._tts.update_options(voice=voice)
        await self.session.say(phrase)
        self._tts.update_options(voice="Ashley")
```

## Expose a function tool for voice switching

Publish a function tool so the LLM can request a different voice by name. The tool delegates to the helper method.

```python
    @function_tool
    async def say_phrase_in_voice_tool(self, phrase: str, voice: str = "Ashley"):
        """Say a phrase in a specific voice"""
        await self.say_phrase_in_voice(phrase, voice)

    async def on_enter(self):
        self.session.generate_reply()
```

## Prewarm VAD for faster connections

Preload the VAD model once per process to reduce connection latency.

```python
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm
```

## Define the rtc session entrypoint

Create the agent first, then create the session using the agent's TTS instance so voice changes are reflected.

```python
@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    agent = SayPhraseInVoiceAgent()

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-5-mini"),
        tts=agent._tts,
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()
```

## Run the server

Start the agent server with the CLI runner.

```python
if __name__ == "__main__":
    cli.run_app(server)
```

## Run it

```bash
python say_in_voice.py console
```

## How it works

1. The agent creates an Inworld TTS instance with a default voice ("Ashley").
2. A helper method temporarily switches voices, speaks the phrase, then restores the default.
3. A function tool exposes this capability to the LLM.
4. When the user asks to say something in a different voice, the LLM calls the tool.

## Full example

```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession, inference, function_tool
from livekit.plugins import silero, inworld

load_dotenv()

logger = logging.getLogger("say-in-voice")
logger.setLevel(logging.INFO)

class SayPhraseInVoiceAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="You are an agent that can say phrases in different voices."
        )
        self._tts = inworld.TTS(voice="Ashley")

    async def say_phrase_in_voice(self, phrase, voice="Hades"):
        self._tts.update_options(voice=voice)
        await self.session.say(phrase)
        self._tts.update_options(voice="Ashley")

    @function_tool
    async def say_phrase_in_voice_tool(self, phrase: str, voice: str = "Ashley"):
        """Say a phrase in a specific voice"""
        await self.say_phrase_in_voice(phrase, voice)

    async def on_enter(self):
        self.session.generate_reply()

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    agent = SayPhraseInVoiceAgent()

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-5-mini"),
        tts=agent._tts,
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
```
