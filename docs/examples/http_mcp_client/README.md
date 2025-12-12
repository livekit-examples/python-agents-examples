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

This example demonstrates how to run an agent as an MCP (Model Context Protocol) client. It connects to an MCP server over HTTP, handles voice I/O, and lets the LLM call MCP tools to fetch data.

## Prerequisites

- Add a `.env` in this directory with your LiveKit credentials:
  ```
  LIVEKIT_URL=your_livekit_url
  LIVEKIT_API_KEY=your_api_key
  LIVEKIT_API_SECRET=your_api_secret
  ```
- Install dependencies:
  ```bash
  pip install "livekit-agents[silero]" python-dotenv
  ```

## Load environment, logging, and define an AgentServer

Start by importing the required modules including the MCP client. The `AgentServer` wraps your application and manages the worker lifecycle.

```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, AgentServer, cli, mcp
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("mcp-agent")
logger.setLevel(logging.INFO)

server = AgentServer()
```

## Prewarm VAD for faster connections

Preload the VAD model once per process. This runs before any sessions start and stores the VAD instance in `proc.userdata` so it can be reused, cutting down on connection latency.

```python
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm
```

## Define a minimal agent

Keep the agent simple—just instructions explaining that it can retrieve data via MCP. The MCP tools become available automatically through the session configuration. Generate a greeting when the agent enters.

```python
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
```

## Define the RTC session entrypoint with MCP configuration

Create an `AgentSession` with VAD and inference strings for STT, LLM, and TTS. The `mcp_servers` parameter accepts a list of MCP server connections—here we use `MCPServerHTTP` to connect to a remote endpoint. The LLM will automatically discover and use the tools exposed by the MCP server.

```python
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
```

## Run the server

The `cli.run_app()` function starts the agent server and manages connections to LiveKit.

```python
if __name__ == "__main__":
    cli.run_app(server)
```

## Run it

```bash
python http_mcp_client.py console
```

## How it works

1. The session connects to an MCP server over HTTP.
2. The LLM automatically discovers tools exposed by the MCP server and can call them to satisfy user requests.

## Full example

```python
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
```
