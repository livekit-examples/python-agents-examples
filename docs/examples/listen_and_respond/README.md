---
title: Listen and Respond
category: basics
tags: [basics, deepgram, openai, cartesia]
difficulty: beginner
description: Shows how to create an agent that can listen to the user and respond.
demonstrates:
  - This is the most basic agent that can listen to the user and respond. This is a good starting point for any agent.
---

This example shows the smallest possible voice agent: load credentials, create a basic STT/LLM/TTS stack, and let it greet and respond to the caller. This is the foundation for most other voice agent examples.

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

## Load environment and define an AgentServer

Start by importing the necessary modules, loading environment variables, and creating an AgentServer instance. The server manages the agent lifecycle and handles incoming connections.

```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, inference, AgentServer, cli
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("listen-and-respond")
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

## Define the agent

Keep your Agent lightweight with just the instructions. The `on_enter` method generates an initial greeting when a participant joins.

```python
class ListenAndRespondAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond.
            """
        )

    async def on_enter(self):
        self.session.generate_reply()
```

## Set up the session

Define the RTC session handler where you configure STT, LLM, and TTS as part of the AgentSession. Start the session with your agent and connect to the room.

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
    agent = ListenAndRespondAgent()

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

Run the agent using the `console` command, which starts the agent in console mode. This mode is useful for testing and debugging. It connects to a mocked LiveKit room so you can test the agent locally before deploying.

```console
python listen_and_respond.py console
```

## How it works

1. Load environment variables and set up a basic voice stack.
2. Prewarm VAD once per process to reduce connection latency.
3. STT transcribes audio, LLM produces a text reply, and TTS speaks it back.
4. Silero VAD handles speech detection so replies wait for end-of-utterance.
5. This pattern is the foundation for most other voice agent examples.

## Full example

```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, inference, AgentServer, cli
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("listen-and-respond")
logger.setLevel(logging.INFO)

class ListenAndRespondAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond.
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
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )
    agent = ListenAndRespondAgent()

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
```
