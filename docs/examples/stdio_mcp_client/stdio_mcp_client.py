"""
---
title: MCP Agent
category: mcp
tags: [mcp, openai, deepgram, cartesia]
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
from livekit.agents import AgentServer, AgentSession, JobContext, JobProcess, cli, Agent, inference, mcp
from livekit.plugins import silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("mcp-agent")

load_dotenv()

class MyAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                """
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
        tts=inference.TTS(model="cartesia/sonic-2", voice="6f84f4b8-58a2-430c-8c79-688dad597532"),
        vad=ctx.proc.userdata["vad"],
        turn_detection=MultilingualModel(),
        mcp_servers=[mcp.MCPServerStdio(command="codex", args=["mcp"], client_session_timeout_seconds=600000)],
        preemptive_generation=True,
    )
    agent = MyAgent()

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
