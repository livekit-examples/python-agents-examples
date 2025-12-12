"""
---
title: Simple Call Answering Agent
category: telephony
tags: [telephony, deepgram, openai, cartesia]
difficulty: beginner
description: Basic agent for handling incoming phone calls with simple conversation
demonstrates:
  - Simple telephony agent setup
  - Basic call handling workflow
  - Standard STT/LLM/TTS configuration
  - Automatic greeting generation on entry
  - Clean agent session lifecycle
---
"""

import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, WorkerOptions, cli, Agent, AgentSession, inference, AgentServer
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("answer-call")
logger.setLevel(logging.INFO)

class SimpleAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent.
            """
        )

    async def on_enter(self):
        self.session.generate_reply()

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session()
async def my_agent(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )
    agent = SimpleAgent()

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
