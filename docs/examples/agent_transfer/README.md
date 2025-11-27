---
title: Long or Short Agent
category: multi-agent
tags: [multi-agent, assemblyai, openai, cartesia]
difficulty: intermediate
description: Shows how to create a multi-agent that can switch between a long and short agent using a function tool.
demonstrates:
  - Creating a multi-agent that can switch between a long and short agent using a function tool.
  - Using a function tool to change the agent.
  - Different agents can have different instructions, models, and tools.
---

In this recipe you will build two agents—one short-winded and one long-winded—and let them swap places mid-call with a
function tool. Each agent has its own instructions while sharing the same inference configuration.

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

Load your environment variables with `load_dotenv()` and set up logging.

```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, Agent, AgentSession, inference, function_tool
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("long-or-short")
logger.setLevel(logging.INFO)
```

## Create the short and long agents

Use inference strings for STT, LLM, and TTS so you do not need provider-specific keys:

```python
class ShortAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond. Be as brief as possible. Arguably too brief.
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
        self.session.say("Hi. It's Short agent.")
```

```python
class LongAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond in overly verbose, flowery, obnoxiously detailed sentences.
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
        self.session.say("Salutations! it is I, your friendly neighborhood long agent.")
```

## Swap agents with a tool call

Expose a function tool on each agent that replaces itself with the other. Both tools reuse the same session so state such
as participants and audio pipelines stay intact:

```python
    @function_tool
    async def change_agent(self):
        """Change the agent to the long agent."""
        self.session.update_agent(LongAgent())
```

```python
    @function_tool
    async def change_agent(self):
        """Change the agent to the short agent."""
        self.session.update_agent(ShortAgent())
```

## Start the session

Launch the short agent by default; the tool can switch to the long agent when invoked:

```python
async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=ShortAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
```

## Run it

```bash
python agent_transfer.py console
```

Ask the agent to "switch to the long agent" or "be more brief" to trigger the function tool and see the swap.

## How it works

1. The short agent starts and greets the caller.
2. A function tool on each agent calls `update_agent` to swap in the other agent.
3. Because the session persists, the call and media pipelines remain active across swaps.
4. Each agent keeps its own instructions and uses the same STT/LLM/TTS inference setup.

For a complete working example, see the code below:

```python
import logging
from dotenv import load_dotenv
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("long-or-short")
logger.setLevel(logging.INFO)

class ShortAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond. Be as brief as possible. Arguably too brief.
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
        self.session.say("Salutations! it is I, your friendly neighborhood long agent.")

    @function_tool
    async def change_agent(self):
        """Change the agent to the short agent."""
        self.session.update_agent(ShortAgent())

async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=ShortAgent(),
        room=ctx.room
    )

    session.once

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
```
