---
title: Tool Calling
category: basics
tags: [tool-calling, openai, deepgram]
difficulty: beginner
description: Shows how to use tool calling in an agent.
demonstrates:
  - Using the most basic form of tool calling in an agent to print to the console
---

This example shows how to use tool calling in an agent.

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
python tool_calling.py console
```

## How it works

- Using the most basic form of tool calling in an agent to print to the console

## Full example

```python
import logging
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, Agent, AgentSession, inference, RunContext, function_tool
from livekit.plugins import silero

logger = logging.getLogger("tool-calling")
logger.setLevel(logging.INFO)

load_dotenv(dotenv_path=Path(__file__).parents[3] / '.env')

class ToolCallingAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice. Don't use any unpronouncable characters.
                Note: If asked to print to the console, use the `print_to_console` function.
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

    @function_tool
    async def print_to_console(self, context: RunContext):
        print("Console Print Success!")
        return None, "I've printed to the console."

    async def on_enter(self):
        self.session.generate_reply()

async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=ToolCallingAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
```
