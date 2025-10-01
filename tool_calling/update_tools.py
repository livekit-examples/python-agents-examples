"""
---
title: Dynamic Tool Updates
category: function-calling
tags: [dynamic-tools, tool-updates, runtime-modification, function-composition]
difficulty: intermediate
description: Demonstrates dynamically adding function tools to agents at runtime
demonstrates:
  - Dynamic function tool creation and addition
  - Runtime agent tool modification with update_tools
  - External function wrapping with function_tool decorator
  - Tool composition and agent enhancement
  - Combining static and dynamic function tools
---
"""

## This is a basic example of how to use function calling.
## To test the function, you can ask the agent to print to the console!

import logging
import random
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.llm import function_tool
from livekit.agents.voice import Agent, AgentSession, RunContext
from livekit.plugins import deepgram, openai, silero

logger = logging.getLogger("function-calling")
logger.setLevel(logging.INFO)

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

class AddFunctionAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice. Don't use any unpronouncable characters.
                Note: If asked to print to the console, use the `print_to_console` function.
            """,
            stt="assemblyai/universal-streaming",
            llm="openai/gpt-4.1-mini",
            tts="cartesia/sonic-2:6f84f4b8-58a2-430c-8c79-688dad597532",
            vad=silero.VAD.load()
        )

    @function_tool
    async def print_to_console(self, context: RunContext):
        print("Console Print Success!")
        return None, "I've printed to the console."

    async def on_enter(self):
        self.session.generate_reply()

async def entrypoint(ctx: JobContext):
    session = AgentSession()
    agent=AddFunctionAgent()

    async def _random_number() -> int:
        num = random.randint(0, 100)
        logger.info(f"random_number called: {num}")
        return num

    await agent.update_tools(
        agent.tools
        + [function_tool(_random_number, name="random_number", description="Get a random number")]
    )

    await session.start(
        agent=agent,
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))