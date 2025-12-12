---
title: Agent Transfer
category: multi-agent
tags: [multi-agent, deepgram, openai, cartesia]
difficulty: intermediate
description: Shows how to switch between agents mid-call using function tools.
demonstrates:
  - Agent transfer using update_agent()
  - Function tools for agent switching
  - Lightweight agent design with instructions and tools only
  - Shared AgentSession across agent swaps
style: two-column
---

This example demonstrates how to build two agents—one short-winded and one long-winded—and let them swap places mid-call with a function tool. Each agent has its own instructions and personality, but they share the same session so the call and media pipelines remain active across swaps.

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

<!-- {% step %} -->
<!-- {% instructions %} -->
## Load environment, logging, and define an AgentServer

Start by loading your environment variables and setting up logging. Define an `AgentServer` which wraps your application and handles the worker lifecycle.
<!-- {% /instructions %} -->

<!-- {% stepCode %} -->
```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, AgentServer, cli, inference, function_tool
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("agent-transfer")
logger.setLevel(logging.INFO)

server = AgentServer()
```
<!-- {% /stepCode %} -->
<!-- {% /step %}-->

<!-- {% step %} -->
<!-- {% instructions %} -->
## Prewarm VAD for faster connections

Preload the VAD model once per process using the `setup_fnc`. This runs before any sessions start and stores the VAD instance in `proc.userdata` so it can be reused across sessions without reloading.
<!-- {% /instructions %} -->

<!-- {% stepCode %} -->
```python
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm
```
<!-- {% /stepCode %} -->
<!-- {% /step %}-->

<!-- {% step %} -->
<!-- {% instructions %} -->
## Create the short and long agents

Define two lightweight agent classes. Each agent only contains its instructions and a function tool to swap to the other agent. The `on_enter` method is called when the agent becomes active and announces itself.
<!-- {% /instructions %} -->

<!-- {% stepCode %} -->
```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, AgentServer, cli, inference, function_tool
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("agent-transfer")
logger.setLevel(logging.INFO)

server = AgentServer()
```
<!-- {% added %} -->
```python
class ShortAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond. Be as brief as possible. Arguably too brief.
            """
        )

    async def on_enter(self):
        self.session.say("Hi. It's Short agent.")

    @function_tool
    async def change_agent(self):
        """Change the agent to the long agent."""
        self.session.update_agent(LongAgent())


class LongAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond in overly verbose, flowery, obnoxiously detailed sentences.
            """
        )

    async def on_enter(self):
        self.session.say("Salutations! It is I, your friendly neighborhood long agent.")

    @function_tool
    async def change_agent(self):
        """Change the agent to the short agent."""
        self.session.update_agent(ShortAgent())
```
<!-- {% /added %} -->
<!-- {% /stepCode %} -->
<!-- {% /step %}-->

<!-- {% step %} -->
<!-- {% instructions %} -->
## Define the RTC session entrypoint

The `@server.rtc_session()` decorator marks this function as the entry point for new sessions. Inside, create an `AgentSession` with your STT, LLM, TTS, and VAD configuration. These settings are shared across both agents since they use the same session. Start the session with the short agent as the default, then connect to the room.
<!-- {% /instructions %} -->

<!-- {% stepCode %} -->
```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, AgentServer, cli, inference, function_tool
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("agent-transfer")
logger.setLevel(logging.INFO)

server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


class ShortAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond. Be as brief as possible. Arguably too brief.
            """
        )

    async def on_enter(self):
        self.session.say("Hi. It's Short agent.")

    @function_tool
    async def change_agent(self):
        """Change the agent to the long agent."""
        self.session.update_agent(LongAgent())


class LongAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond in overly verbose, flowery, obnoxiously detailed sentences.
            """
        )

    async def on_enter(self):
        self.session.say("Salutations! It is I, your friendly neighborhood long agent.")

    @function_tool
    async def change_agent(self):
        """Change the agent to the short agent."""
        self.session.update_agent(ShortAgent())
```
<!-- {% added %} -->
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

    await session.start(agent=ShortAgent(), room=ctx.room)
    await ctx.connect()
```
<!-- {% /added %} -->
<!-- {% /stepCode %} -->
<!-- {% /step %}-->

<!-- {% step %} -->
<!-- {% instructions %} -->
## Run the server

The `cli.run_app()` function starts the agent server. It manages the worker lifecycle, connects to LiveKit, and processes incoming jobs.
<!-- {% /instructions %} -->

<!-- {% stepCode %} -->
```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, AgentServer, cli, inference, function_tool
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("agent-transfer")
logger.setLevel(logging.INFO)

server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


class ShortAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond. Be as brief as possible. Arguably too brief.
            """
        )

    async def on_enter(self):
        self.session.say("Hi. It's Short agent.")

    @function_tool
    async def change_agent(self):
        """Change the agent to the long agent."""
        self.session.update_agent(LongAgent())


class LongAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond in overly verbose, flowery, obnoxiously detailed sentences.
            """
        )

    async def on_enter(self):
        self.session.say("Salutations! It is I, your friendly neighborhood long agent.")

    @function_tool
    async def change_agent(self):
        """Change the agent to the short agent."""
        self.session.update_agent(ShortAgent())


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

    await session.start(agent=ShortAgent(), room=ctx.room)
    await ctx.connect()
```
<!-- {% added %} -->
```python
if __name__ == "__main__":
    cli.run_app(server)
```
<!-- {% /added %} -->
<!-- {% /stepCode %} -->
<!-- {% /step %}-->

## Run it

Run the agent using the `console` command, which starts the agent in console mode. This mode is useful for testing and debugging. It connects to a mocked LiveKit room so you can test the agent locally before deploying.

```bash
python agent_transfer.py console
```

Ask the agent to "switch to the long agent" or "be more brief" to trigger the function tool and see the swap.

If you want to test your agent in a real room, start it in dev mode instead:

```bash
python agent_transfer.py dev
```

## How it works

1. The short agent starts and greets the caller.
2. Each agent exposes a `change_agent` function tool that calls `update_agent()` to swap in the other agent.
3. Because the session persists, the call and media pipelines remain active across swaps.
4. Each agent keeps its own instructions and personality while sharing the same STT/LLM/TTS configuration.

## Full example

```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, AgentServer, cli, inference, function_tool
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("agent-transfer")
logger.setLevel(logging.INFO)


class ShortAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond. Be as brief as possible. Arguably too brief.
            """
        )

    async def on_enter(self):
        self.session.say("Hi. It's Short agent.")

    @function_tool
    async def change_agent(self):
        """Change the agent to the long agent."""
        self.session.update_agent(LongAgent())


class LongAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond in overly verbose, flowery, obnoxiously detailed sentences.
            """
        )

    async def on_enter(self):
        self.session.say("Salutations! It is I, your friendly neighborhood long agent.")

    @function_tool
    async def change_agent(self):
        """Change the agent to the short agent."""
        self.session.update_agent(ShortAgent())


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

    await session.start(agent=ShortAgent(), room=ctx.room)
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
```
