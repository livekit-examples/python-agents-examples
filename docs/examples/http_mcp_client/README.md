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

This example shows how to use a LiveKit Agent as an MCP client.

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

## Run it

```bash
python http_mcp_client.py console
```

## How it works

- Connecting to a local MCP server as a client.
- Connecting to a remote MCP server as a client.
- Using a function tool to retrieve data from the MCP server.

## Full example

```python
import logging
from dotenv import load_dotenv
from pathlib import Path
from livekit.agents import JobContext, WorkerOptions, cli, Agent, AgentSession, inference, mcp
from livekit.plugins import silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("mcp-agent")

load_dotenv(dotenv_path=Path(__file__).parents[3] / '.env')

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

async def entrypoint(ctx: JobContext):
    session = AgentSession(
        vad=silero.VAD.load(),
        stt="assemblyai/universal-streaming",
        llm="openai/gpt-4.1-mini",
        tts="cartesia/sonic-2:6f84f4b8-58a2-430c-8c79-688dad597532",
        turn_detection=MultilingualModel(),
        mcp_servers=[mcp.MCPServerHTTP(url="https://shayne.app/mcp",)],
    )

    await session.start(agent=MyAgent(), room=ctx.room)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
```
