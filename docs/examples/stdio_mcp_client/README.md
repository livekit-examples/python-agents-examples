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

This example shows how to connect a LiveKit voice agent to an MCP (Model Context Protocol) server. MCP allows the agent to access external tools and data sources. In this case, the agent connects to a local Codex instance via stdio, enabling voice-based interaction with the Codex coding assistant.

## Prerequisites

- Add a `.env` in this directory with your LiveKit credentials:
  ```
  LIVEKIT_URL=your_livekit_url
  LIVEKIT_API_KEY=your_api_key
  LIVEKIT_API_SECRET=your_api_secret
  ```
- Install dependencies:
  ```bash
  pip install "livekit-agents[silero,deepgram,openai,cartesia]" python-dotenv
  ```
- Have an MCP server available (this example uses Codex)

## Set up logging and create the AgentServer

Load environment variables and configure logging. Create an AgentServer to manage the agent lifecycle.

```python
import logging
from dotenv import load_dotenv
from livekit.agents import AgentServer, AgentSession, JobContext, JobProcess, cli, Agent, inference, mcp
from livekit.plugins import silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("mcp-agent")

load_dotenv()

server = AgentServer()
```

## Prewarm VAD for faster connections

Preload the VAD model once per process. This runs before any sessions start and stores the VAD instance in `proc.userdata` so it can be reused.

```python
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm
```

## Define a lightweight agent

Keep the Agent lightweight with just instructions. The MCP server provides the tools, so the agent doesn't need to define any function tools itself. The instructions explain how to interact with the MCP server.

```python
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
```

## Define the RTC session entrypoint with MCP server

Create the AgentSession with STT, LLM, TTS, VAD, and the MCP server configuration. The `mcp_servers` parameter accepts a list of MCP server connections—here we use `MCPServerStdio` to connect to a local Codex process.

```python
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
```

## Run the server

The `cli.run_app()` function starts the agent server, manages the worker lifecycle, and processes incoming jobs.

```python
if __name__ == "__main__":
    cli.run_app(server)
```

## Run it

Run the agent using the `console` command for local testing:

```bash
python stdio_mcp_client.py console
```

To test with a real LiveKit room, use dev mode:

```bash
python stdio_mcp_client.py dev
```

## How it works

1. The agent connects to the MCP server (Codex) via stdio when the session starts.
2. The MCP server exposes tools that the LLM can call.
3. When users speak, their requests are transcribed and sent to the LLM.
4. The LLM can invoke MCP tools to perform actions like code generation or file operations.
5. Tool results are incorporated into the response and spoken back to the user.

## Full example

```python
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
```
