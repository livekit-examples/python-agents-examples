"""
---
title: Agent Transfer
category: multi-agent
tags: [multi-agent, deepgram, openai, cartesia]
difficulty: intermediate
description: Shows how to switch between agents mid-call using function tools.
demonstrates:
  - Agent transfer using update_agent()
  - Function tools for agent switching
  - Lightweight agent design with instructions and tools only
  - Shared AgentSession across agent swaps
---
"""
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, AgentServer, cli, inference, function_tool
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("agent-transfer")
logger.setLevel(logging.INFO)


class ShortAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond. Be as brief as possible. Arguably too brief.
            """
        )

    async def on_enter(self):
        self.session.say("Hi. It's Short agent.")

    @function_tool
    async def change_agent(self):
        """Change the agent to the long agent."""
        self.session.update_agent(LongAgent())


class LongAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond in overly verbose, flowery, obnoxiously detailed sentences.
            """
        )

    async def on_enter(self):
        self.session.say("Salutations! It is I, your friendly neighborhood long agent.")

    @function_tool
    async def change_agent(self):
        """Change the agent to the short agent."""
        self.session.update_agent(ShortAgent())


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

    await session.start(agent=ShortAgent(), room=ctx.room)
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
