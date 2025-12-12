"""
---
title: Tool Calling
category: basics
tags: [tool-calling, deepgram, openai, cartesia]
difficulty: beginner
description: Shows how to use tool calling in an agent.
demonstrates:
  - Using the most basic form of tool calling in an agent to print to the console
---
"""

import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession, inference, RunContext, function_tool
from livekit.plugins import silero

logger = logging.getLogger("tool-calling")
logger.setLevel(logging.INFO)

load_dotenv()

class ToolCallingAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice. Don't use any unpronouncable characters.
                Note: If asked to print to the console, use the `print_to_console` function.
            """
        )

    @function_tool
    async def print_to_console(self, context: RunContext):
        print("Console Print Success!")
        return None, "I've printed to the console."

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

    await session.start(agent=ToolCallingAgent(), room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
