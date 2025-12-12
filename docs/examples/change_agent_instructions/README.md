---
title: Change Agent Instructions
category: basics
tags: [instructions, deepgram, openai, cartesia]
difficulty: beginner
description: Shows how to change the instructions of an agent at runtime.
demonstrates:
  - Changing agent instructions after the agent has started using update_instructions()
  - Conditional logic based on participant attributes
---

This example shows how to update an agent's instructions at runtime. The agent detects when a participant appears to be calling from a phone (by checking if their name contains digits) and adjusts its instructions accordingly while keeping the same media pipeline running.

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

Start by loading your environment variables and setting up logging. Define an `AgentServer` which wraps your application and handles the worker lifecycle.

```python
import logging
import re
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, AgentServer, cli, inference
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("change-agent-instructions")
logger.setLevel(logging.INFO)

server = AgentServer()
```

## Prewarm VAD for faster connections

Preload the VAD model once per process using the `setup_fnc`. This runs before any sessions start and stores the VAD instance in `proc.userdata` so it can be reused across sessions.

```python
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm
```

## Create the agent with runtime instruction updates

Define a lightweight agent class with just instructions. The `on_enter` method checks if the participant name looks like a phone number (contains 4+ consecutive digits) and updates the instructions to reference the phone context.

```python
class ChangeInstructionsAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond.
            """
        )

    async def on_enter(self):
        # Treat any participant name containing 4 consecutive digits as a phone number.
        if self.session.participant.name and re.search(r"\d{4}", self.session.participant.name):
            await self.update_instructions("""
                You are a helpful agent speaking on the phone.
            """)
        self.session.generate_reply()
```

## Define the RTC session entrypoint

The `@server.rtc_session()` decorator marks this function as the entry point for new sessions. Create an `AgentSession` with your STT, LLM, TTS, and VAD configuration, then start the session and connect to the room.

```python
@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(agent=ChangeInstructionsAgent(), room=ctx.room)
    await ctx.connect()
```

## Run the server

The `cli.run_app()` function starts the agent server. It manages the worker lifecycle, connects to LiveKit, and processes incoming jobs.

```python
if __name__ == "__main__":
    cli.run_app(server)
```

## Run it

Run the agent using the `console` command for local testing:

```bash
python change_agent_instructions.py console
```

To test with real telephony, start in dev mode and call your agent after purchasing a [phone number](https://docs.livekit.io/sip/cloud/phone-numbers/):

```bash
python change_agent_instructions.py dev
```

## How it works

1. The agent loads LiveKit credentials from a local `.env`.
2. It starts with default instructions and media settings.
3. On enter, SIP callers (detected by digits in participant name) trigger `update_instructions()` to switch to phone-specific guidance.
4. The agent generates the first reply with the updated instructions in place.

## Full example

```python
import logging
import re
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, AgentServer, cli, inference
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("change-agent-instructions")
logger.setLevel(logging.INFO)


class ChangeInstructionsAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond.
            """
        )

    async def on_enter(self):
        # Treat any participant name containing 4 consecutive digits as a phone number.
        if self.session.participant.name and re.search(r"\d{4}", self.session.participant.name):
            await self.update_instructions("""
                You are a helpful agent speaking on the phone.
            """)
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
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(agent=ChangeInstructionsAgent(), room=ctx.room)
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
```
