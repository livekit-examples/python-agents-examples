---
title: Basic Event
category: events
tags: [events, openai, deepgram, cartesia]
difficulty: beginner
description: Shows how to use events in an agent to trigger actions.
demonstrates:
  - Using events in an agent to trigger actions
  - Using on() to register an event listener
  - Using off() to unregister an event listener
  - Using once() to register an event listener that will only be triggered once
---

This example demonstrates how to wire up a simple event system inside an agent. The agent registers listeners, fires an event on entry, and shows how to unsubscribe and use one-shot listeners while a LiveKit voice session is running.

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

## Load environment, logging, and define an AgentServer

Start by loading your environment variables and setting up logging. Define an `AgentServer` which wraps your application and handles the worker lifecycle.

```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, AgentServer, cli, inference
from livekit.plugins import silero
from livekit.rtc import EventEmitter

load_dotenv()

logger = logging.getLogger("basic-event")
logger.setLevel(logging.INFO)

server = AgentServer()
```

## Prewarm VAD for faster connections

Preload the VAD model once per process using the `setup_fnc`. This runs before any sessions start and stores the VAD instance in `proc.userdata` so it can be reused across sessions.

```python
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm
```

## Define the agent with event hooks

Create a lightweight agent with an `EventEmitter`. Attach the `greet` handler to the emitter in `__init__` so the agent can react to custom events while the session runs.

```python
class SimpleAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond.
            """
        )
        self.emitter.on('greet', self.greet)

    emitter = EventEmitter[str]()

    def greet(self, name):
        self.session.say(f"Hello, {name}!")
```

## Emit, unsubscribe, and one-shot listeners

Inside `on_enter`, emit a greeting twice to show how `off()` stops future callbacks. The second emit is skipped because we unsubscribed the handler.

```python
    async def on_enter(self):
        self.emitter.emit('greet', 'Alice')
        self.emitter.off('greet', self.greet)
        # This will not trigger the greet function, because we unregistered it with the line above
        # Comment out the 'off' line above to hear the agent greet Bob as well as Alice
        self.emitter.emit('greet', 'Bob')
```

## Define the RTC session entrypoint

The `@server.rtc_session()` decorator marks this function as the entry point for new sessions. Create the agent instance and register additional event handlers, including a `once()` handler that fires only once.

```python
@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    agent = SimpleAgent()
    agent.emitter.on('greet', agent.greet)

    # We'll print this log once, because we registered it with the once method
    agent.emitter.once('greet', lambda name: print(f"[Once] Greeted {name}"))

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()
```

## Run the server

The `cli.run_app()` function starts the agent server.

```python
if __name__ == "__main__":
    cli.run_app(server)
```

## Run it

```bash
python basic_event.py console
```

## How it works

- The agent registers event callbacks before the session starts.
- `emit()` triggers any registered callbacks; `off()` removes them.
- `once()` runs a callback a single time and cleans up automatically.
- The demo fires events when the agent enters so you can see subscription behavior immediately.

## Full example

```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, AgentServer, cli, inference
from livekit.plugins import silero
from livekit.rtc import EventEmitter

load_dotenv()

logger = logging.getLogger("basic-event")
logger.setLevel(logging.INFO)


class SimpleAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond.
            """
        )
        self.emitter.on('greet', self.greet)

    emitter = EventEmitter[str]()

    def greet(self, name):
        self.session.say(f"Hello, {name}!")

    async def on_enter(self):
        self.emitter.emit('greet', 'Alice')
        self.emitter.off('greet', self.greet)
        # This will not trigger the greet function, because we unregistered it with the line above
        # Comment out the 'off' line above to hear the agent greet Bob as well as Alice
        self.emitter.emit('greet', 'Bob')


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    agent = SimpleAgent()
    agent.emitter.on('greet', agent.greet)

    # We'll print this log once, because we registered it with the once method
    agent.emitter.once('greet', lambda name: print(f"[Once] Greeted {name}"))

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
```
