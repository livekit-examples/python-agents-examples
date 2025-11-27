---
title: Exit Message
category: basics
tags: [exit, message, openai, deepgram]
difficulty: beginner
description: Shows how to use the `on_exit` method to take an action when the agent exits.
demonstrates:
  - Use the `on_exit` method to take an action when the agent exits
---

This example shows how to use the `on_exit` method to take an action when the agent exits.

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
python exit_message.py console
```

## How it works

- Use the `on_exit` method to take an action when the agent exits

## Full example

```python
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, Agent, AgentSession, inference, function_tool
from livekit.plugins import silero

load_dotenv(dotenv_path=Path(__file__).parents[3] / '.env')

logger = logging.getLogger("exit-message")
logger.setLevel(logging.INFO)

class GoodbyeAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent.
                When the user wants to stop talking to you, use the end_session function to close the session.
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
    async def end_session(self):
        """When the user wants to stop talking to you, use this function to close the session."""
        await self.session.drain()
        await self.session.aclose()

    async def on_exit(self):
        await self.session.say("Goodbye!")

async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=GoodbyeAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
```
