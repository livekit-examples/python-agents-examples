"""
---
title: Event Emitters
category: events
tags: [events, deepgram, openai, cartesia]
difficulty: beginner
description: Shows how to use event emitters in an agent to trigger actions.
demonstrates:
  - Using event emitters in an agent to trigger actions like welcome and farewell messages
  - Custom event handling with EventEmitter
---
"""
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
        # Simulate participant joining and leaving
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
