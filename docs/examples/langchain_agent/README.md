---
title: LangChain Agent
category: integrations
tags: [langchain, openai]
difficulty: beginner
description: Shows how to use a LangChain agent with tools in a LiveKit voice agent.
demonstrates:
  - Using create_agent from langchain.agents to build a tool-calling agent
  - Defining LangChain tools with the @tool decorator
  - Using a custom llm_node to stream only AI responses and filter tool messages
---

This example shows how to use a LangChain agent with tools as the LLM backend for a LiveKit voice agent. The agent is created with `create_agent` from `langchain.agents` and given a `get_weather` tool. A custom `llm_node` override shows how you can modify the graph output if needed.

**Ask the agent for the weather in your city**

> **Latency note:** The `LLMAdapter` uses LangGraph's streaming mode to minimise time-to-first-token, but care should be taken when porting LangChain workflows that were not originally designed for voice use cases. For more information on handling long-running operations and providing a better user experience, see the [user feedback documentation](https://docs.livekit.io/agents/logic/external-data/#user-feedback).

## Prerequisites

- Add a `.env` in this directory with your LiveKit and OpenAI credentials:
  ```
  LIVEKIT_URL=your_livekit_url
  LIVEKIT_API_KEY=your_api_key
  LIVEKIT_API_SECRET=your_api_secret
  OPENAI_API_KEY=your_openai_api_key
  ```
- Install dependencies:
  ```bash
  pip install "livekit-agents[silero]" livekit-plugins-langchain langchain langchain-openai python-dotenv
  ```

## Load environment and define the AgentServer

Import the necessary modules and load environment variables.

```python
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.messages import AIMessageChunk
from langchain_openai import ChatOpenAI
from livekit.agents import (
    Agent, AgentServer, AgentSession, JobContext, JobProcess, cli, inference, llm,
)
from livekit.plugins import langchain, silero

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

## Define a LangChain tool

Use the `@tool` decorator to define a tool that the LangChain agent can call. Replace the stub implementation with a real API call for production use.  Note that this is a [LangChain tool](https://docs.langchain.com/oss/python/langchain/tools), not a LiveKit tool.

```python
@tool
def get_weather(city: str) -> str:
    """Get the current weather for a given city.

    Args:
        city: The name of the city to get weather for.
    """
    # Stub implementation - replace with a real weather API call
    return f"The weather in {city} is sunny and 72 degrees Fahrenheit."
```

## Create the LangChain agent

Use `create_agent` to build a tool-calling agent backed by `ChatOpenAI`. The returned compiled graph can be used with the `LLMAdapter`.

```python
ASSISTANT_INSTRUCTIONS = """You are a helpful voice AI assistant with access to tools.
You can look up the weather for any city when asked.
Your responses are concise, to the point, and without any complex formatting or punctuation including emojis, asterisks, or other symbols."""

_agent_graph = create_agent(
    model=ChatOpenAI(model="gpt-4.1-mini", temperature=0.7),
    tools=[get_weather],
)
```

## Define the agent with a custom llm_node

Override `llm_node` to stream from the LangChain agent graph directly. The `LLMAdapter` streams all message types including `ToolMessage` content, which would cause tool results to be spoken before the final response. This override filters the stream to only yield `AIMessageChunk` instances.

```python
class LangChainAgent(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=ASSISTANT_INSTRUCTIONS)

    async def llm_node(self, chat_ctx, tools, model_settings=None):
        state = langchain.LLMAdapter(graph=_agent_graph).chat(
            chat_ctx=chat_ctx, tools=[]
        )
        lc_messages = state._chat_ctx_to_state()

        async for chunk, _metadata in _agent_graph.astream(
            lc_messages, stream_mode="messages"
        ):
            if isinstance(chunk, AIMessageChunk) and chunk.content:
                yield llm.ChatChunk(
                    id=chunk.id or "",
                    delta=llm.ChoiceDelta(
                        role="assistant", content=chunk.content
                    ),
                )
```

## Create the RTC session entrypoint

Create an `AgentSession` with the LangGraph workflow wrapped in `langchain.LLMAdapter`. The adapter automatically converts LiveKit's chat context to LangChain message types.

```python
@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=langchain.LLMAdapter(graph=_agent_graph),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
    )

    await session.start(agent=LangChainAgent(), room=ctx.room)
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
python langchain_agent.py console
```

## How it works

1. `create_agent` builds a LangGraph-based agent with the `get_weather` tool.
2. When the user asks about weather, the LLM calls the tool and then formulates a response using the result.
3. The custom `llm_node` streams from the graph with `stream_mode="messages"`, filtering to only yield `AIMessageChunk` instances. This prevents `ToolMessage` content from being spoken as duplicate output.
4. The `LLMAdapter` on the session handles converting LiveKit's chat context to LangChain messages via `_chat_ctx_to_state()`.

## Full example

```python
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.messages import AIMessageChunk
from langchain_openai import ChatOpenAI
from livekit.agents import (
    Agent, AgentServer, AgentSession, JobContext, JobProcess, cli, inference, llm,
)
from livekit.plugins import langchain, silero

load_dotenv()

ASSISTANT_INSTRUCTIONS = """You are a helpful voice AI assistant with access to tools.
You can look up the weather for any city when asked.
Your responses are concise, to the point, and without any complex formatting or punctuation including emojis, asterisks, or other symbols."""


@tool
def get_weather(city: str) -> str:
    """Get the current weather for a given city.

    Args:
        city: The name of the city to get weather for.
    """
    # Stub implementation - replace with a real weather API call
    return f"The weather in {city} is sunny and 72 degrees Fahrenheit."


_agent_graph = create_agent(
    model=ChatOpenAI(model="gpt-4.1-mini", temperature=0.7),
    tools=[get_weather],
)


class LangChainAgent(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=ASSISTANT_INSTRUCTIONS)

    async def llm_node(self, chat_ctx, tools, model_settings=None):
        state = langchain.LLMAdapter(graph=_agent_graph).chat(
            chat_ctx=chat_ctx, tools=[]
        )
        lc_messages = state._chat_ctx_to_state()

        async for chunk, _metadata in _agent_graph.astream(
            lc_messages, stream_mode="messages"
        ):
            if isinstance(chunk, AIMessageChunk) and chunk.content:
                yield llm.ChatChunk(
                    id=chunk.id or "",
                    delta=llm.ChoiceDelta(
                        role="assistant", content=chunk.content
                    ),
                )


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=langchain.LLMAdapter(graph=_agent_graph),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
    )

    await session.start(agent=LangChainAgent(), room=ctx.room)
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
```
