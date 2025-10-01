"""
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
"""
import logging
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import silero
from livekit.rtc import EventEmitter

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

logger = logging.getLogger("basic-event")
logger.setLevel(logging.INFO)

class SimpleAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond.
            """,
            stt="assemblyai/universal-streaming",
            llm="openai/gpt-4.1-mini",
            tts="cartesia/sonic-2:6f84f4b8-58a2-430c-8c79-688dad597532",
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