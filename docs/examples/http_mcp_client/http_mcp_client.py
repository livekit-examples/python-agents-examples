"""
---
title: MCP Agent
category: mcp
tags: [mcp, deepgram, openai, cartesia]
difficulty: beginner
description: Shows how to use a LiveKit Agent as an MCP client.
demonstrates:
  - Connecting to a remote MCP server as a client
  - Using MCP tools with voice-based interaction
---
"""
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, AgentServer, cli, mcp
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("mcp-agent")
logger.setLevel(logging.INFO)


class MyAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You can retrieve data via the MCP server. The interface is voice-based: "
                "accept spoken user queries and respond with synthesized speech."
            ),
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
        vad=ctx.proc.userdata["vad"],
        stt="deepgram/nova-3-general",
        llm="openai/gpt-4.1-mini",
        tts="cartesia/sonic-2:6f84f4b8-58a2-430c-8c79-688dad597532",
        mcp_servers=[mcp.MCPServerHTTP(url="https://shayne.app/mcp")],
    )

    await session.start(agent=MyAgent(), room=ctx.room)
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
