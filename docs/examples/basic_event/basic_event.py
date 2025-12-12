"""
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
"""
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
