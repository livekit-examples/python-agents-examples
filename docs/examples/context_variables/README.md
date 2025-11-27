---
title: Context Variables
category: basics
tags: [context, variables, openai, deepgram]
difficulty: beginner
description: Shows how to give an agent context about the user using simple variables.
demonstrates:
  - Using context variables from a simple dictionary
---

This example shows how to give an agent context about the user using simple variables.

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
python context_variables.py console
```

## How it works

- Using context variables from a simple dictionary

## Full example

```python
import logging
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, Agent, AgentSession
from livekit.plugins import openai, deepgram, silero

load_dotenv(dotenv_path=Path(__file__).parents[3] / '.env')

logger = logging.getLogger("context-variables")
logger.setLevel(logging.INFO)

class ContextAgent(Agent):
    def __init__(self, context_vars=None) -> None:
        instructions = """
            You are a helpful agent. The user's name is {name}.
            They are {age} years old and live in {city}.
        """

        if context_vars:
            instructions = instructions.format(**context_vars)

        super().__init__(
            instructions=instructions,
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
    context_variables = {
        "name": "Shayne",
        "age": 35,
        "city": "Toronto"
    }

    session = AgentSession()

    await session.start(
        agent=ContextAgent(context_vars=context_variables),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
```
