"""
---
title: Exit Message
category: basics
tags: [exit, message, deepgram, openai, cartesia]
difficulty: beginner
description: Shows how to use the on_exit method to take an action when the agent exits.
demonstrates:
  - Using the on_exit method to take an action when the agent exits
  - Using function tools to end sessions gracefully
---
"""
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, AgentServer, cli, inference, function_tool
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("exit-message")
logger.setLevel(logging.INFO)


class GoodbyeAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent.
                When the user wants to stop talking to you, use the end_session function to close the session.
            """
        )

    @function_tool
    async def end_session(self):
        """When the user wants to stop talking to you, use this function to close the session."""
        await self.session.drain()
        await self.session.aclose()

    async def on_exit(self):
        await self.session.say("Goodbye!")


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

    await session.start(agent=GoodbyeAgent(), room=ctx.room)
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
