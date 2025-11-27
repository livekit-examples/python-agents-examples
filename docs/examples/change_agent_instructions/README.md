---
title: Change Agent Instructions
category: basics
tags: [instructions, assemblyai, openai, cartesia]
difficulty: beginner
description: Shows how to change the instructions of an agent.
demonstrates:
  - Changing agent instructions after the agent has started using `update_instructions`
---

In this recipe you will start an agent and then update its instructions on the fly. The example tweaks the voice prompts
for SIP callers while keeping the same media pipeline (STT/LLM/TTS) running.

## Prerequisites

- Add a `.env` in this directory with your LiveKit credentials:
  ```
  LIVEKIT_URL=your_livekit_url
  LIVEKIT_API_KEY=your_api_key
  LIVEKIT_API_SECRET=your_api_secret
  ```
- Install dependencies in one line:
  ```bash
  pip install "livekit-agents[silero]" python-dotenv
  ```

## Load configuration and logging

Use `load_dotenv()` to read the local environment file and set up logging:

```python
import logging
import re
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, Agent, AgentSession
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("change-agent-instructions")
logger.setLevel(logging.INFO)
```

## Create the agent with inference strings

Define the agent using LiveKit inference strings for STT/LLM/TTS so you do not need provider-specific keys:

```python
class ChangeInstructionsAgent(Agent):
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
```

## Change instructions at runtime

When a participant name looks like a phone number (any 4 digits in a row), update the instructions to reference the phone
context, then start the initial reply:

```python
    async def on_enter(self):
        if self.session.participant.name and re.search(r"\d{4}", self.session.participant.name):
            await self.update_instructions("""
                You are a helpful agent speaking on the phone.
            """)
        self.session.generate_reply()
```

## Start the session

Launch the agent and connect it to the room:

```python
async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=ChangeInstructionsAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
```

## Run it

```bash
python change_agent_instructions.py console
```

## How it works

1. The agent loads LiveKit credentials from a local `.env`.
2. It starts with default instructions and media settings using inference strings.
3. On enter, SIP callers trigger `update_instructions` to switch to phone-specific guidance.
4. The agent generates the first reply with the updated instructions in place.

## Full example

```python
import logging
import re
from dotenv import load_dotenv
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("change-agent-instructions")
logger.setLevel(logging.INFO)

class ChangeInstructionsAgent(Agent):
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
        if self.session.participant.name and re.search(r"\d{4}", self.session.participant.name):
            await self.update_instructions("""
                You are a helpful agent speaking on the phone.
            """)
        self.session.generate_reply()

async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=ChangeInstructionsAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
```
