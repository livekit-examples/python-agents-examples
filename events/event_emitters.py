"""
---
title: Event Emitters
category: events
tags: [events, openai, assemblyai]
difficulty: beginner
description: Shows how to use event emitters in an agent to trigger actions.
demonstrates:
  - Using event emitters in an agent to trigger actions like welcome and farewell messages for the sake of example (even though there are already events for this)
---
"""
import logging
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import silero
from livekit.rtc import EventEmitter
import asyncio

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

logger = logging.getLogger("event-emitters")
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