---
title: Exit Message
category: basics
tags: [exit, message, deepgram, openai, cartesia]
difficulty: beginner
description: Shows how to use the on_exit method to take an action when the agent exits.
demonstrates:
  - Using the on_exit method to take an action when the agent exits
  - Using function tools to end sessions gracefully
---

This example demonstrates how to add a clean shutdown flow to an agent. The agent exposes a function tool to end the session and speaks a goodbye message from `on_exit`.

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

Start by importing the required modules and setting up logging to watch the session lifecycle. The `AgentServer` wraps your application and manages the worker lifecycle.

```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, AgentServer, cli, inference, function_tool
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("exit-message")
logger.setLevel(logging.INFO)

server = AgentServer()
```

## Prewarm VAD for faster connections

Preload the VAD model once per process. This runs before any sessions start and stores the VAD instance in `proc.userdata` so it can be reused, cutting down on connection latency.

```python
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm
```

## Define an agent with an end-session tool

The agent is instructed to call a function tool when the user wants to end the conversation. The `end_session` tool drains any pending work from the session and then closes the media pipelines gracefully.

```python
class GoodbyeAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent.
                When the user wants to stop talking to you, use the end_session function to close the session.
            """
        )

    @function_tool
    async def end_session(self):
        """When the user wants to stop talking to you, use this function to close the session."""
        await self.session.drain()
        await self.session.aclose()
```

## Say goodbye on exit

Use the `on_exit` hook to speak a final message after the session closes. This runs even when the tool initiated the close, giving you a chance to say goodbye before the connection ends.

```python
    async def on_exit(self):
        await self.session.say("Goodbye!")
```

## Define the RTC session entrypoint

Create an `AgentSession` with STT, LLM, TTS, and VAD configuration. Start the session with the agent and connect to the room. When the user asks to hang up, the LLM will invoke `end_session` to close the call gracefully.

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

    await session.start(agent=GoodbyeAgent(), room=ctx.room)
    await ctx.connect()
```

## Run the server

The `cli.run_app()` function starts the agent server and manages connections to LiveKit.

```python
if __name__ == "__main__":
    cli.run_app(server)
```

## Run it

```bash
python exit_message.py console
```

## How it works

1. A function tool ends the session when the user asks to hang up.
2. The agent drains outstanding work, closes the session, and then runs `on_exit`.
3. `on_exit` plays a final TTS message before the connection ends.

## Full example

```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, AgentServer, cli, inference, function_tool
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("exit-message")
logger.setLevel(logging.INFO)


class GoodbyeAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent.
                When the user wants to stop talking to you, use the end_session function to close the session.
            """
        )

    @function_tool
    async def end_session(self):
        """When the user wants to stop talking to you, use this function to close the session."""
        await self.session.drain()
        await self.session.aclose()

    async def on_exit(self):
        await self.session.say("Goodbye!")


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

    await session.start(agent=GoodbyeAgent(), room=ctx.room)
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
```
