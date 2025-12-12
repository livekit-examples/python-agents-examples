"""
---
title: Listen and Respond
category: basics
tags: [basics, deepgram, openai, cartesia]
difficulty: beginner
description: Shows how to create an agent that can listen to the user and respond.
demonstrates:
  - This is the most basic agent that can listen to the user and respond. This is a good starting point for any agent.
---
"""

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
