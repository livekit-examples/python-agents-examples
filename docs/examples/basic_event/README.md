---
title: Basic Event
category: events
tags: [events, openai, assemblyai]
difficulty: beginner
description: Shows how to use events in an agent to trigger actions.
demonstrates:
  - Using events in an agent to trigger actions
  - Using `on` to register an event listener
  - Using `off` to unregister an event listener
  - Using `once` to register an event listener that will only be triggered once
---

This example shows how to use events in an agent to trigger actions.

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

## Run it

```bash
python basic_event.py console
```

## How it works

- Using events in an agent to trigger actions
- Using `on` to register an event listener
- Using `off` to unregister an event listener
- Using `once` to register an event listener that will only be triggered once

## Full example

```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, Agent, AgentSession
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
            """,
            stt=inference.STT(
                model="assemblyai/universal-streaming",
                language="en"
            ),
            llm=inference.LLM(
                model="openai/gpt-5-mini",
                provider="openai",
            ),
            tts=inference.TTS(
                model="cartesia/sonic-3",
                voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
            ),
            vad=silero.VAD.load()
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

async def entrypoint(ctx: JobContext):
    agent = SimpleAgent()
    agent.emitter.on('greet', agent.greet)

    # We'll print this log once, because we registered it with the once method
    agent.emitter.once('greet', lambda name: print(f"[Once] Greeted {name}"))

    session = AgentSession()
    await session.start(
        agent=agent,
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
```
