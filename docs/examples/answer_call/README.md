---
title: Simple Call Answering Agent
category: telephony
tags: [telephony, assemblyai, openai, cartesia]
difficulty: beginner
description: Basic agent for handling incoming phone calls with simple conversation
demonstrates:
  - Simple telephony agent setup
  - Basic call handling workflow
  - Standard STT/LLM/TTS configuration
  - Automatic greeting generation on entry
  - Clean agent session lifecycle
---

This example answers inbound phone calls using the same agent pattern as any other voice agent. No SIP-specific code is
required: once you point a LiveKit phone number at a dispatch rule, SIP callers are delivered into the room and the
running agent greets them.

## Prerequisites

- Buy a phone number in the LiveKit dashboard and create a dispatch rule that targets your worker:
  - Buy a number: Telephony → Phone Numbers → Buy number → Create dispatch rule
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

## Load environment and logging

```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, Agent, AgentSession
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("answer-call")
logger.setLevel(logging.INFO)
```

## Define the agent

Use inference strings for STT/LLM/TTS; no extra provider keys are needed:

```python
class SimpleAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent.
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
```

## Start the session

```python
async def entrypoint(ctx: JobContext):
    session = AgentSession()
    agent = SimpleAgent()

    await session.start(
        agent=agent,
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
```

## Run it

```bash
python answer_call.py console
```

## How inbound calls connect

1. An inbound call hits your LiveKit number.
2. The dispatch rule attaches the SIP participant to your room.
3. If the worker is running, the agent is already in the room and responds immediately—no special SIP handling needed.

## Full example

```python
import logging
from dotenv import load_dotenv
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("answer-call")
logger.setLevel(logging.INFO)

class SimpleAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent.
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
    agent = SimpleAgent()

    await session.start(
        agent=agent,
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
```
