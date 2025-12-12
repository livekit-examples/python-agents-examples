---
title: Tool Calling
category: basics
tags: [tool-calling, deepgram, openai, cartesia]
difficulty: beginner
description: Shows how to use tool calling in an agent.
demonstrates:
  - Using the most basic form of tool calling in an agent to print to the console
---

This example shows how to use tool calling in an agent. The agent has a simple function tool that prints a message to the console when invoked. Ask the agent to "print to the console" to see it in action.

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

## Load environment and define the AgentServer

Import the necessary modules, load environment variables, and create an AgentServer.

```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession, inference, RunContext, function_tool
from livekit.plugins import silero

logger = logging.getLogger("tool-calling")
logger.setLevel(logging.INFO)

load_dotenv()

server = AgentServer()
```

## Prewarm VAD for faster connections

Preload the VAD model once per process to reduce connection latency.

```python
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm
```

## Define the agent with a function tool

Create a lightweight Agent that only contains instructions and a function tool. The `@function_tool` decorator exposes the method as a callable tool to the LLM. The method returns a tuple of `(result, message)` where the message is what the agent says after calling the tool.

```python
class ToolCallingAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice. Don't use any unpronouncable characters.
                Note: If asked to print to the console, use the `print_to_console` function.
            """
        )

    @function_tool
    async def print_to_console(self, context: RunContext):
        print("Console Print Success!")
        return None, "I've printed to the console."

    async def on_enter(self):
        self.session.generate_reply()
```

## Create the RTC session entrypoint

Create an AgentSession with STT/LLM/TTS/VAD configured, start the session with the agent, and connect to the room.

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

    await session.start(agent=ToolCallingAgent(), room=ctx.room)
    await ctx.connect()
```

## Run the server

The `cli.run_app()` function starts the agent server and manages the worker lifecycle.

```python
if __name__ == "__main__":
    cli.run_app(server)
```

## Run it

```console
python tool_calling.py console
```

## How it works

1. The agent starts and generates an initial greeting via `on_enter`.
2. When the user asks to print to the console, the LLM calls the `print_to_console` function.
3. The function executes and prints "Console Print Success!" to the terminal.
4. The agent speaks "I've printed to the console" as confirmation.

## Full example

```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession, inference, RunContext, function_tool
from livekit.plugins import silero

logger = logging.getLogger("tool-calling")
logger.setLevel(logging.INFO)

load_dotenv()

class ToolCallingAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice. Don't use any unpronouncable characters.
                Note: If asked to print to the console, use the `print_to_console` function.
            """
        )

    @function_tool
    async def print_to_console(self, context: RunContext):
        print("Console Print Success!")
        return None, "I've printed to the console."

    async def on_enter(self):
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

    await session.start(agent=ToolCallingAgent(), room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
```
