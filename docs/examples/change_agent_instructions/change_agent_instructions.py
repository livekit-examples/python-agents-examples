"""
---
title: Change Agent Instructions
category: basics
tags: [instructions, deepgram, openai, cartesia]
difficulty: beginner
description: Shows how to change the instructions of an agent at runtime.
demonstrates:
  - Changing agent instructions after the agent has started using update_instructions()
  - Conditional logic based on participant attributes
---
"""

import logging
import re
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, AgentServer, cli, inference
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("change-agent-instructions")
logger.setLevel(logging.INFO)


class ChangeInstructionsAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond.
            """
        )

    async def on_enter(self):
        # Treat any participant name containing 4 consecutive digits as a phone number.
        if self.session.participant.name and re.search(r"\d{4}", self.session.participant.name):
            await self.update_instructions("""
                You are a helpful agent speaking on the phone.
            """)
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

    await session.start(agent=ChangeInstructionsAgent(), room=ctx.room)
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
