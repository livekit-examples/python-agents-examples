---
title: Dynamic Tool Updates
category: function-calling
tags: [dynamic-tools, tool-updates, runtime-modification, function-composition, deepgram, openai, cartesia]
difficulty: intermediate
description: Demonstrates dynamically adding function tools to agents at runtime
demonstrates:
  - Dynamic function tool creation and addition
  - Runtime agent tool modification with update_tools
  - External function wrapping with function_tool decorator
  - Tool composition and agent enhancement
  - Combining static and dynamic function tools
---

This example demonstrates dynamically adding function tools to agents at runtime. The agent starts with a static `print_to_console` tool defined via decorator, then a `random_number` tool is added dynamically before the session starts.

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

## Load environment and create the AgentServer

Import the necessary modules, load environment variables, and create an AgentServer.

```python
import logging
import random
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession, inference, RunContext, function_tool
from livekit.plugins import silero

logger = logging.getLogger("function-calling")
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

## Define the agent with a static function tool

Create a lightweight Agent that contains instructions and a static function tool. The `@function_tool` decorator exposes the method as a callable tool to the LLM.

```python
class AddFunctionAgent(Agent):
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

## Add dynamic tools at runtime

Define an external function and wrap it with `function_tool()` to add it dynamically. Use `agent.update_tools()` to combine existing tools with the new one.

```python
async def _random_number() -> int:
    num = random.randint(0, 100)
    logger.info(f"random_number called: {num}")
    return num

await agent.update_tools(
    agent.tools
    + [function_tool(_random_number, name="random_number", description="Get a random number")]
)
```

## Create the RTC session entrypoint

Create an AgentSession with STT/LLM/TTS/VAD configured, add the dynamic tool, start the session, and connect to the room.

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
    agent = AddFunctionAgent()

    async def _random_number() -> int:
        num = random.randint(0, 100)
        logger.info(f"random_number called: {num}")
        return num

    await agent.update_tools(
        agent.tools
        + [function_tool(_random_number, name="random_number", description="Get a random number")]
    )

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()
```

## Run it

```console
python update_tools.py console
```

## How it works

1. The agent is created with a static `print_to_console` tool defined via decorator.
2. Before the session starts, a `random_number` function is wrapped with `function_tool()`.
3. `agent.update_tools()` merges the existing tools with the new dynamic tool.
4. The LLM now has access to both tools during the conversation.
5. Ask the agent to "print to the console" or "give me a random number" to test both tools.

## Full example

```python
import logging
import random
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession, inference, RunContext, function_tool
from livekit.plugins import silero

logger = logging.getLogger("function-calling")
logger.setLevel(logging.INFO)

load_dotenv()

class AddFunctionAgent(Agent):
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
    agent = AddFunctionAgent()

    async def _random_number() -> int:
        num = random.randint(0, 100)
        logger.info(f"random_number called: {num}")
        return num

    await agent.update_tools(
        agent.tools
        + [function_tool(_random_number, name="random_number", description="Get a random number")]
    )

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
```
