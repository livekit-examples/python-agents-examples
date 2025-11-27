---
title: Listen and Respond
category: basics
tags: [listen, respond, openai, deepgram]
difficulty: beginner
description: Shows how to create an agent that can listen to the user and respond.
demonstrates:
  - This is the most basic agent that can listen to the user and respond. This is a good starting point for any agent.
---

This example shows how to create an agent that can listen to the user and respond.

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
python listen_and_respond.py console
```

## How it works

- This is the most basic agent that can listen to the user and respond. This is a good starting point for any agent.

## Full example

```python
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, Agent, AgentSession
from livekit.plugins import silero

load_dotenv(dotenv_path=Path(__file__).parents[3] / '.env')

logger = logging.getLogger("listen-and-respond")
logger.setLevel(logging.INFO)

class ListenAndRespondAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond.
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

    async def on_enter(self):
        self.session.generate_reply()

async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=ListenAndRespondAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
```
