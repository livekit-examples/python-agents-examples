---
title: Uninterruptable Agent
category: basics
tags: [interruptions, allow_interruptions, agent_configuration]
difficulty: beginner
description: Agent configured to complete responses without user interruptions
demonstrates:
  - Setting allow_interruptions=False in agent configuration
  - Testing interruption handling behavior
  - Agent-initiated conversation with on_enter
---

This example Agent configured to complete responses without user interruptions.

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
python uninterruptable.py console
```

## How it works

- Setting allow_interruptions=False in agent configuration
- Testing interruption handling behavior
- Agent-initiated conversation with on_enter

## Full example

```python
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, Agent, AgentSession
from livekit.plugins import silero

load_dotenv(dotenv_path=Path(__file__).parents[3] / '.env')

class UninterruptableAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice who is not interruptable.
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
            allow_interruptions=False,
            vad=silero.VAD.load()
        )

    async def on_enter(self):
        self.session.generate_reply(user_input="Say something somewhat long and boring so I can test if you're interruptable.")

async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=UninterruptableAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
```
