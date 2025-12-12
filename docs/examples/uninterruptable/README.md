---
title: Uninterruptable Agent
category: basics
tags: [interruptions, allow_interruptions, agent_configuration, deepgram, openai, cartesia]
difficulty: beginner
description: Agent configured to complete responses without user interruptions
demonstrates:
  - Setting allow_interruptions=False in agent configuration
  - Testing interruption handling behavior
  - Agent-initiated conversation with on_enter
---

This example configures an agent to finish speaking even if the user talks over it by disabling interruptions. The agent also seeds the first user input so you can test the behavior immediately.

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

Load environment variables so the audio plugins can authenticate. Create an AgentServer to manage sessions.

```python
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession, inference
from livekit.plugins import silero

load_dotenv()

server = AgentServer()
```

## Prewarm VAD for faster connections

Preload the VAD model once per process to reduce connection latency.

```python
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm
```

## Create a non-interruptable agent

Set `allow_interruptions=False` when constructing the agent. The agent class is lightweight—only instructions and the interruption setting are defined here.

```python
class UninterruptableAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice who is not interruptable.
            """,
            allow_interruptions=False
        )

    async def on_enter(self):
        self.session.generate_reply(user_input="Say something somewhat long and boring so I can test if you're interruptable.")
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

    await session.start(agent=UninterruptableAgent(), room=ctx.room)
    await ctx.connect()
```

## Run it

```console
python uninterruptable.py console
```

## How it works

1. `allow_interruptions=False` keeps TTS playback intact even if new speech arrives.
2. `on_enter` seeds a first prompt so you can test the behavior without speaking first.
3. The rest of the media pipeline remains unchanged from a standard agent.
4. This setting is useful when you want to ensure an announcement completes before listening again.

## Full example

```python
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession, inference
from livekit.plugins import silero

load_dotenv()

class UninterruptableAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice who is not interruptable.
            """,
            allow_interruptions=False
        )

    async def on_enter(self):
        self.session.generate_reply(user_input="Say something somewhat long and boring so I can test if you're interruptable.")

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

    await session.start(agent=UninterruptableAgent(), room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
```
