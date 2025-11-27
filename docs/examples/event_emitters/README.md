---
title: Event Emitters
category: events
tags: [events, openai, assemblyai]
difficulty: beginner
description: Shows how to use event emitters in an agent to trigger actions.
demonstrates:
  - Using event emitters in an agent to trigger actions like welcome and farewell messages for the sake of example (even though there are already events for this)
---

This example shows how to use event emitters in an agent to trigger actions.

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
python event_emitters.py console
```

## How it works

- Using event emitters in an agent to trigger actions like welcome and farewell messages for the sake of example (even though there are already events for this)

## Full example

```python
import logging
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, Agent, AgentSession
from livekit.plugins import silero
from livekit.rtc import EventEmitter
import asyncio

load_dotenv(dotenv_path=Path(__file__).parents[3] / '.env')

logger = logging.getLogger("event-emitters")
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
        self.emitter.on('participant_joined', self.welcome_participant)
        self.emitter.on('participant_left', self.farewell_participant)

    emitter = EventEmitter[str]()

    def welcome_participant(self, name: str):
        self.session.say(f"Welcome, {name}! Glad you could join.")

    def farewell_participant(self, name: str):
        self.session.say(f"Goodbye, {name}. See you next time!")

    async def on_enter(self):
        # Simulate participant joining and leaving
        self.emitter.emit('participant_joined', 'Alice')
        asyncio.get_event_loop().call_later(
            10,
            lambda: self.emitter.emit('participant_left', 'Alice')
        )

async def entrypoint(ctx: JobContext):
    agent = SimpleAgent()
    agent.emitter.on('participant_joined', agent.welcome_participant)
    agent.emitter.on('participant_left', agent.farewell_participant)

    session = AgentSession()
    await session.start(
        agent=agent,
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
```
