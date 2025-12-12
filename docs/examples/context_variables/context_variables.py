"""
---
title: Context Variables
category: basics
tags: [context, variables, deepgram, openai, cartesia]
difficulty: beginner
description: Shows how to give an agent context about the user using simple variables.
demonstrates:
  - Using context variables from a simple dictionary
  - Formatting instructions with user-specific data
---
"""

import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, AgentServer, cli, inference
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("context-variables")
logger.setLevel(logging.INFO)


class ContextAgent(Agent):
    def __init__(self, context_vars=None) -> None:
        instructions = """
            You are a helpful agent. The user's name is {name}.
            They are {age} years old and live in {city}.
        """

        if context_vars:
            instructions = instructions.format(**context_vars)

        super().__init__(instructions=instructions)

    async def on_enter(self):
        self.session.generate_reply()


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    context_variables = {
        "name": "Shayne",
        "age": 35,
        "city": "Toronto"
    }

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(agent=ContextAgent(context_vars=context_variables), room=ctx.room)
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
