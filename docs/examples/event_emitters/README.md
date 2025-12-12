---
title: Event Emitters
category: events
tags: [events, deepgram, openai, cartesia]
difficulty: beginner
description: Shows how to use event emitters in an agent to trigger actions.
demonstrates:
  - Using event emitters in an agent to trigger custom actions like welcome and farewell messages
  - Custom event handling with EventEmitter
---

This example demonstrates how to use a lightweight event emitter to simulate participants joining and leaving a call. The agent listens for those events and speaks a welcome or farewell message.

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

Start by importing the required modules and setting up logging to follow the simulated events. The `AgentServer` wraps your application and manages the worker lifecycle.

```python
import logging
import asyncio
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, AgentServer, cli, inference
from livekit.plugins import silero
from livekit.rtc import EventEmitter

load_dotenv()

logger = logging.getLogger("event-emitters")
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

## Create the agent with custom events

Define a lightweight agent with an `EventEmitter` class attribute. Attach handlers for `participant_joined` and `participant_left` events in the constructor so they're ready when events fire.

```python
class EventEmittersAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond.
            """
        )
        self.emitter.on('participant_joined', self.welcome_participant)
        self.emitter.on('participant_left', self.farewell_participant)

    emitter = EventEmitter[str]()

    def welcome_participant(self, name: str):
        self.session.say(f"Welcome, {name}! Glad you could join.")

    def farewell_participant(self, name: str):
        self.session.say(f"Goodbye, {name}. See you next time!")
```

## Emit welcome and farewell messages

In `on_enter`, emit the join event immediately and schedule a leave event 10 seconds later to demonstrate both callbacks. Usually this callback will do something in the background, but here we're scheduling it so that you can hear it fire while you're still in the call.

```python
    async def on_enter(self):
        self.emitter.emit('participant_joined', 'Alice')
        asyncio.get_event_loop().call_later(
            10,
            lambda: self.emitter.emit('participant_left', 'Alice')
        )
```

## Define the RTC session entrypoint

Create the agent and register additional event handlers from outside the class. Then create an `AgentSession` with STT, LLM, TTS, and VAD configuration, start the session, and connect to the room.

```python
@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    agent = EventEmittersAgent()
    agent.emitter.on('participant_joined', agent.welcome_participant)
    agent.emitter.on('participant_left', agent.farewell_participant)

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

The `cli.run_app()` function starts the agent server and manages connections to LiveKit.

```python
if __name__ == "__main__":
    cli.run_app(server)
```

## Run it

```bash
python event_emitters.py console
```

## How it works

1. An `EventEmitter` lives on the agent to handle simple custom events.
2. Handlers call `session.say()` to speak greetings and farewells.
3. `on_enter` fires a join event immediately and schedules a later leave event so both paths run and you can hear them.

## Full example

```python
import logging
import asyncio
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, AgentServer, cli, inference
from livekit.plugins import silero
from livekit.rtc import EventEmitter

load_dotenv()

logger = logging.getLogger("event-emitters")
logger.setLevel(logging.INFO)


class EventEmittersAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond.
            """
        )
        self.emitter.on('participant_joined', self.welcome_participant)
        self.emitter.on('participant_left', self.farewell_participant)

    emitter = EventEmitter[str]()

    def welcome_participant(self, name: str):
        self.session.say(f"Welcome, {name}! Glad you could join.")

    def farewell_participant(self, name: str):
        self.session.say(f"Goodbye, {name}. See you next time!")

    async def on_enter(self):
        self.emitter.emit('participant_joined', 'Alice')
        asyncio.get_event_loop().call_later(
            10,
            lambda: self.emitter.emit('participant_left', 'Alice')
        )


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    agent = EventEmittersAgent()
    agent.emitter.on('participant_joined', agent.welcome_participant)
    agent.emitter.on('participant_left', agent.farewell_participant)

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
