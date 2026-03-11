---
title: LangChain Deep Agent
category: integrations
tags: [langchain, openai, deepagents]
difficulty: intermediate
description: Shows how to use a LangChain deep agent with planning and subagents in a LiveKit voice agent.
demonstrates:
  - Using create_deep_agent from the deepagents library
  - Delegating work to a subagent for weather research
  - Using built-in planning (write_todos)
  - Using a custom llm_node to stream only AI responses and filter tool messages
---

This example shows how to build a trip planning voice assistant using a LangChain deep agent. The agent uses built-in deep agent capabilities: `write_todos` for breaking a trip plan into steps, and a `weather_researcher` subagent for looking up weather. A custom `get_attractions` tool provides tourist information.

**Ask the agent to plan your trip to Paris**

This demonstrates how deep agents go beyond simple tool calling by orchestrating multi-step workflows with planning and delegation — all driven by voice.

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
  pip install "livekit-agents[silero]" livekit-plugins-langchain deepagents langchain-openai python-dotenv
  ```

## Load environment and define the AgentServer

Import the necessary modules and load environment variables.

```python
from dotenv import load_dotenv
from deepagents import create_deep_agent
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

## Define custom tools

Define tools the agent and its subagents can call. The `get_weather` tool is given to the weather subagent, while `get_attractions` is given to the main agent.

```python
@tool
def get_weather(city: str) -> str:
    """Get the current weather for a given city.

    Args:
        city: The name of the city to get weather for.
    """
    # Stub implementation - replace with a real weather API call
    return f"The weather in {city} is sunny and 72 degrees Fahrenheit."


@tool
def get_attractions(city: str) -> str:
    """Get popular tourist attractions for a given city.

    Args:
        city: The name of the city to get attractions for.
    """
    # Stub implementation - replace with a real attractions API call
    attractions = {
        "paris": "Eiffel Tower, Louvre Museum, Notre-Dame Cathedral, Champs-Elysees",
        "london": "Big Ben, Tower of London, British Museum, Buckingham Palace",
        "tokyo": "Shibuya Crossing, Senso-ji Temple, Tokyo Tower, Meiji Shrine",
    }
    result = attractions.get(city.lower(), "Various local landmarks and cultural sites")
    return f"Popular attractions in {city}: {result}"
```

## Create the deep agent with a subagent

Use `create_deep_agent` to build the agent. The `subagents` parameter defines a `weather_researcher` that the main agent can delegate to using the built-in `task` tool. The main agent also has access to the built-in `write_todos` tool for planning.

```python
ASSISTANT_INSTRUCTIONS = """You are a trip planning voice assistant.
When the user asks you to plan a trip, you should:
1. Use write_todos to break the planning into steps.
2. Delegate weather research to the weather_researcher subagent using the task tool.
3. Summarize the plan back to the user.

Your spoken responses are concise, to the point, and without any complex formatting or punctuation including emojis, asterisks, or other symbols."""

_agent_graph = create_deep_agent(
    model=ChatOpenAI(model="gpt-4.1-mini", temperature=0.7),
    tools=[get_attractions],
    system_prompt=ASSISTANT_INSTRUCTIONS,
    subagents=[
        {
            "name": "weather_researcher",
            "description": "Looks up the current weather for a city. Delegate to this subagent when you need weather information for trip planning.",
            "system_prompt": "You are a weather research assistant. Use the get_weather tool to look up weather for the requested city and return a brief summary.",
            "tools": [get_weather],
        },
    ],
)
```

## Define the agent with a custom llm_node

Override `llm_node` to stream from the LangChain agent graph directly. The `LLMAdapter` streams all message types including `ToolMessage` content, which would cause tool results to be spoken before the final response. This override filters the stream to only yield `AIMessageChunk` instances.

```python
class DeepAgentVoice(Agent):
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

    await session.start(agent=DeepAgentVoice(), room=ctx.room)
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
python langchain_deepagent.py console
```

Try asking: "Plan a trip to Paris" or "What's the weather in Tokyo?"

## How it works

1. `create_deep_agent` builds a LangGraph-based agent with built-in tools for planning and subagent delegation, plus the custom `get_attractions` tool and a `weather_researcher` subagent.
2. When the user asks to plan a trip, the agent uses `write_todos` to break it into steps, delegates weather lookup to the subagent via the `task` tool, and calls `get_attractions` for tourist information.
3. The custom `llm_node` streams from the graph with `stream_mode="messages"`, filtering to only yield `AIMessageChunk` instances. This prevents all the intermediate tool results from being spoken — only the agent's final summary is heard.

## Full example

```python
from dotenv import load_dotenv
from deepagents import create_deep_agent
from langchain.tools import tool
from langchain_core.messages import AIMessageChunk
from langchain_openai import ChatOpenAI
from livekit.agents import (
    Agent, AgentServer, AgentSession, JobContext, JobProcess, cli, inference, llm,
)
from livekit.plugins import langchain, silero

load_dotenv()

ASSISTANT_INSTRUCTIONS = """You are a trip planning voice assistant.
When the user asks you to plan a trip, you should:
1. Use write_todos to break the planning into steps.
2. Delegate weather research to the weather_researcher subagent using the task tool.
3. Summarize the plan back to the user.

Your spoken responses are concise, to the point, and without any complex formatting or punctuation including emojis, asterisks, or other symbols."""


@tool
def get_weather(city: str) -> str:
    """Get the current weather for a given city.

    Args:
        city: The name of the city to get weather for.
    """
    # Stub implementation - replace with a real weather API call
    return f"The weather in {city} is sunny and 72 degrees Fahrenheit."


@tool
def get_attractions(city: str) -> str:
    """Get popular tourist attractions for a given city.

    Args:
        city: The name of the city to get attractions for.
    """
    # Stub implementation - replace with a real attractions API call
    attractions = {
        "paris": "Eiffel Tower, Louvre Museum, Notre-Dame Cathedral, Champs-Elysees",
        "london": "Big Ben, Tower of London, British Museum, Buckingham Palace",
        "tokyo": "Shibuya Crossing, Senso-ji Temple, Tokyo Tower, Meiji Shrine",
    }
    result = attractions.get(city.lower(), "Various local landmarks and cultural sites")
    return f"Popular attractions in {city}: {result}"


_agent_graph = create_deep_agent(
    model=ChatOpenAI(model="gpt-4.1-mini", temperature=0.7),
    tools=[get_attractions],
    system_prompt=ASSISTANT_INSTRUCTIONS,
    subagents=[
        {
            "name": "weather_researcher",
            "description": "Looks up the current weather for a city. Delegate to this subagent when you need weather information for trip planning.",
            "system_prompt": "You are a weather research assistant. Use the get_weather tool to look up weather for the requested city and return a brief summary.",
            "tools": [get_weather],
        },
    ],
)


class DeepAgentVoice(Agent):
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

    await session.start(agent=DeepAgentVoice(), room=ctx.room)
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
```
