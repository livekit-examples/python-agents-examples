"""
---
title: Long or Short Agent
category: multi-agent
tags: [multi-agent, assemblyai, openai, cartesia]
difficulty: intermediate
description: Shows how to create a multi-agent that can switch between a long and short agent using a function tool.
demonstrates:
  - Creating a multi-agent that can switch between a long and short agent using a function tool.
  - Using a function tool to change the agent.
  - Different agents can have different instructions, models, and tools.
---
"""
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, Agent, AgentSession, inference, function_tool
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("long-or-short")
logger.setLevel(logging.INFO)

class ShortAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond. Be as brief as possible. Arguably too brief.
            """,
            stt=inference.STT(
                model="assemblyai/universal-streaming",
                language="en"
            ),
            llm=inference.LLM(
                model="openai/gpt-5-mini",
                provider="openai",
            ),
            tts=inference.TTS(
                model="cartesia/sonic-3",
                voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
            ),
            vad=silero.VAD.load()
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
            """,
            stt=inference.STT(
                model="assemblyai/universal-streaming",
                language="en"
            ),
            llm=inference.LLM(
                model="openai/gpt-5-mini",
                provider="openai",
            ),
            tts=inference.TTS(
                model="cartesia/sonic-3"
            ),
            vad=silero.VAD.load()
        )

    async def on_enter(self):
        self.session.say("Salutations! it is I, your friendly neighborhood long agent.")

    @function_tool
    async def change_agent(self):
        """Change the agent to the short agent."""
        self.session.update_agent(ShortAgent())

async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=ShortAgent(),
        room=ctx.room
    )

    session.once

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
