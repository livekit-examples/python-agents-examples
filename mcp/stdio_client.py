"""
---
title: MCP Agent
category: mcp
tags: [mcp, openai, assemblyai]
difficulty: beginner
description: Shows how to use a LiveKit Agent as an MCP client.
demonstrates:
  - Connecting to a local MCP server as a client.
  - Connecting to a remote MCP server as a client.
  - Using a function tool to retrieve data from the MCP server.
---
"""
import logging
from dotenv import load_dotenv
from pathlib import Path
from livekit.agents import Agent, AgentSession, JobContext, WorkerOptions, cli, mcp
from livekit.plugins import silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("mcp-agent")

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

class MyAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                f"""
                You can retrieve data via the MCP server. The interface is voice-based:
                accept spoken user queries and respond with synthesized speech.
                The MCP server is a codex instance running on the local machine.

                When you call the codex MCP server, you should use the following parameters:
                - approval-policy: never
                - sandbox: workspace-write
                - prompt: [user_prompt_goes_here]
                """

            ),
        )

    async def on_enter(self):
        self.session.generate_reply()

async def entrypoint(ctx: JobContext):
    session = AgentSession(
        vad=silero.VAD.load(),
        stt="assemblyai/universal-streaming",
        llm="openai/gpt-4.1-mini",
        tts="cartesia/sonic-2:6f84f4b8-58a2-430c-8c79-688dad597532",
        turn_detection=MultilingualModel(),
        mcp_servers=[mcp.MCPServerStdio(command="codex", args=["mcp"], client_session_timeout_seconds=600000)],
    )

    await session.start(agent=MyAgent(), room=ctx.room)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))