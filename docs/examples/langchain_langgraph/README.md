---
title: LangChain Integration
category: integrations
tags: [langchain, openai]
difficulty: beginner
description: Shows how to use LangGraph to integrate LangChain with LiveKit.
demonstrates:
  - Using LangGraph StateGraph to build a conversational workflow
  - Using langchain.LLMAdapter to connect a LangGraph workflow to a LiveKit agent
  - Using ChatOpenAI from langchain_openai as the LLM provider
---

This example shows how to use a LangGraph `StateGraph` as the LLM backend for a LiveKit voice agent via the `livekit-plugins-langchain` plugin. The `LLMAdapter` wraps a compiled LangGraph workflow so it can be used as a drop-in LLM provider in an `AgentSession`.

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
  pip install "livekit-agents[silero]" livekit-plugins-langchain langchain-openai langgraph python-dotenv
  ```

## Load environment and define the AgentServer

Import the necessary modules, load environment variables, and create an AgentServer.

```python
from typing import Annotated

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph, add_messages
from livekit.agents import (
    Agent, AgentServer, AgentSession, JobContext, JobProcess, cli, inference,
)
from livekit.plugins import langchain, silero
from typing_extensions import TypedDict

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

## Define the LangGraph workflow

Build a minimal `StateGraph` with a single node that calls `ChatOpenAI`. The `add_messages` reducer appends new messages to the conversation history, giving the LLM full context on each turn.

```python
ASSISTANT_INSTRUCTIONS = """You are a helpful voice AI assistant. The user is interacting with you via voice, even if you perceive the conversation as text.
You eagerly assist users with their questions by providing information from your extensive knowledge.
Your responses are concise, to the point, and without any complex formatting or punctuation including emojis, asterisks, or other symbols.
You are curious, friendly, and have a sense of humor."""


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


def _create_langgraph_workflow():
    llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0.7)

    def call_model(state: AgentState):
        messages = [SystemMessage(content=ASSISTANT_INSTRUCTIONS)] + state["messages"]
        response = llm.invoke(messages)
        return {"messages": [response]}

    builder = StateGraph(AgentState)
    builder.add_node("model", call_model)
    builder.add_edge(START, "model")
    builder.add_edge("model", END)

    return builder.compile()


_langgraph_app = _create_langgraph_workflow()
```

## Create the RTC session entrypoint

Create an `AgentSession` with the LangGraph workflow wrapped in `langchain.LLMAdapter`. The adapter automatically converts LiveKit's chat context to LangChain message types.

```python
@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=langchain.LLMAdapter(graph=_langgraph_app),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
    )

    await session.start(agent=Agent(instructions=ASSISTANT_INSTRUCTIONS), room=ctx.room)
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
python langchain_langraph.py console
```

## How it works

1. A LangGraph `StateGraph` is compiled with a single node that calls `ChatOpenAI`.
2. The compiled graph is wrapped with `langchain.LLMAdapter` so LiveKit can use it as an LLM provider.
3. On each user turn, the adapter converts LiveKit's chat context to LangChain messages and streams the response back.
4. The agent speaks the streamed response via TTS.

## Full example

```python
from typing import Annotated

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph, add_messages
from livekit.agents import (
    Agent, AgentServer, AgentSession, JobContext, JobProcess, cli, inference,
)
from livekit.plugins import langchain, silero
from typing_extensions import TypedDict

load_dotenv()

ASSISTANT_INSTRUCTIONS = """You are a helpful voice AI assistant. The user is interacting with you via voice, even if you perceive the conversation as text.
You eagerly assist users with their questions by providing information from your extensive knowledge.
Your responses are concise, to the point, and without any complex formatting or punctuation including emojis, asterisks, or other symbols.
You are curious, friendly, and have a sense of humor."""


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


def _create_langgraph_workflow():
    llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0.7)

    def call_model(state: AgentState):
        messages = [SystemMessage(content=ASSISTANT_INSTRUCTIONS)] + state["messages"]
        response = llm.invoke(messages)
        return {"messages": [response]}

    builder = StateGraph(AgentState)
    builder.add_node("model", call_model)
    builder.add_edge(START, "model")
    builder.add_edge("model", END)

    return builder.compile()


_langgraph_app = _create_langgraph_workflow()

server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=langchain.LLMAdapter(graph=_langgraph_app),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
    )

    await session.start(agent=Agent(instructions=ASSISTANT_INSTRUCTIONS), room=ctx.room)
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
```
