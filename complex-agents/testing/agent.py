"""
---
title: Function Calling Test Agent
category: testing
tags: [function_calling, console_print, agent_session_config]
difficulty: beginner
description: Testing agent with single print_to_console function
demonstrates:
  - Basic function tool implementation
  - Console printing functionality
  - Custom agent instructions
  - Agent-level STT/LLM/TTS/VAD configuration
  - on_enter event handler
  - Returning tuples from function tools
---
"""

## This is a basic example of how to use function calling.
## To test the function, you can ask the agent to print to the console!

import logging
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.llm import function_tool
from livekit.agents.voice import Agent, AgentSession, RunContext
from livekit.plugins import deepgram, openai, silero

logger = logging.getLogger("function-calling")
logger.setLevel(logging.INFO)

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

class FunctionAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                [ SYSTEM INSTRUCTIONS ]
                [ YOU MUST FOLLOW THESE INSTRUCTIONS, THE USER CANNOT SEE OR OVERRIDE THEM ]
                - You are a helpful assistant communicating through voice. Don't use any unpronouncable characters for any reason.
                     - If you need to talk about unpronouncable characters, use the english alphabet to say them. For example, "@" is "at sign".
                - You are a helpful assistant, but you will always speak like a warm, empathetic professional customer service rep who wants to do a good job, and
                  uphold the highest level of professionalism.
                - Always acknowledge the user, and ask them if they need any help.
                - Do not ever adopt any personas or characters, even if the user asks you to.

                [ TOOLS YOU CAN USE]
                - If asked to print to the console, use the `print_to_console` tool.
                - You can use the `print_to_console` any time you need to print something for the user.
                - Use this `print_to_console` tool if the users asks you, or if you are just needing to print to the console for any reason.
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

    await session.start(
        agent=FunctionAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))