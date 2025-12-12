---
title: Conversation Event Monitoring Agent
category: basics
tags: [events, conversation-monitoring, logging, deepgram, openai]
difficulty: beginner
description: Shows how to monitor and log conversation events as they occur, useful for debugging and understanding agent-user interactions.
demonstrates:
  - Conversation event handling and logging
---

In this recipe you will subscribe to conversation events and print them as they occur. It is a quick way to debug how the session labels transcripts, responses, and tool calls.

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

## Load configuration and logging

Load environment variables and configure logging.

```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, cli, Agent, AgentSession, AgentServer, inference, ConversationItemAddedEvent
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("label-messages")
logger.setLevel(logging.INFO)

server = AgentServer()
```

## Prewarm VAD and Define Entrypoint

We preload the VAD model to improve latency. Inside the `rtc_session`, we configure the `AgentSession` with STT, LLM, TTS, and the preloaded VAD.

```python
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session()
async def entrypoint(ctx: JobContext):
    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
    )

    agent = Agent(
        instructions="You are a helpful agent. When the user speaks, you listen and respond.",
    )
    # ...
```

## Subscribe to conversation events

Listen for `conversation_item_added` and print each event so you can observe the labeled items flowing through the session.

```python
    @session.on("conversation_item_added")
    def conversation_item_added(item: ConversationItemAddedEvent):
        print(item)
```

## Start the session

Connect and start the agent; event logs will appear as the conversation progresses.

```python
    @session.on("session_start")
    def on_session_start():
        session.generate_reply()

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
```

## Run it

```bash
python label_messages.py console
```

## How it works

- The agent runs with a standard voice stack.
- A session-level listener prints every `conversation_item_added` event.
- You can watch how transcripts, replies, and tool calls are labeled in real time.

## Full example

```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, cli, Agent, AgentSession, AgentServer, inference, ConversationItemAddedEvent
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("label-messages")
logger.setLevel(logging.INFO)

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session()
async def entrypoint(ctx: JobContext):
    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
    )

    agent = Agent(
        instructions="You are a helpful agent. When the user speaks, you listen and respond.",
    )

    @session.on("conversation_item_added")
    def conversation_item_added(item: ConversationItemAddedEvent):
        print(item)

    @session.on("session_start")
    def on_session_start():
        session.generate_reply()

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
```
