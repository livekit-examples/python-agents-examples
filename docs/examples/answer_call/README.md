---
title: Simple Call Answering Agent
category: telephony
tags: [telephony, assemblyai, openai, cartesia]
difficulty: beginner
description: Basic agent for handling incoming phone calls with simple conversation
style: step-by-step
githubUrl: https://github.com/livekit-examples/python-agents-examples/docs/examples/answer_call/answer_call.py
demonstrates:
  - Simple telephony agent setup
  - Basic call handling workflow
  - Standard STT/LLM/TTS configuration
  - Automatic greeting generation on entry
  - Clean agent session lifecycle
---

This example is a basic agent that can answer inbound phone calls. This doesn't require any SIP-specific code. When you point a LiveKit phone number at a dispatch rule, SIP callers are automatically delivered into the room and the running agent greets them.

## Prerequisites

- Buy a phone number in the LiveKit dashboard and create a dispatch rule that targets your worker:
  - Buy a number: Telephony → Phone Numbers → Buy number → Create dispatch rule
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

Start by importing the necessary modules and setting up the basic agent server. Load environment variables and configure logging for debugging.
<!-- {% /instructions %} -->

<!-- {% stepCode %} -->
<!-- {% added %} -->
```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, AgentServer, cli, inference
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("answer-call")
logger.setLevel(logging.INFO)

server = AgentServer()
```
<!-- {% /added %} -->
<!-- {% /stepCode %} -->
<!-- {% /step %}-->

<!-- {% step %} -->
<!-- {% instructions %} -->
## Define the agent and session

Keep your Agent lightweight by only including the instructions. Preload VAD so that it runs once per process to cut down on connection latency.

Define STT, LLM, and TTS as a part of your AgentSession inside the RTC session. Start your session with your agent and connect to the room.
<!-- {% /instructions %} -->

<!-- {% stepCode %} -->
```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, AgentServer, cli, inference
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("answer-call")
logger.setLevel(logging.INFO)

server = AgentServer()
```

<!-- {% added %} -->
```python
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

class SimpleAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent.
            """
        )

    async def on_enter(self):
        self.session.generate_reply()


@server.rtc_session()
async def my_agent(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )
    agent = SimpleAgent()

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()
```
<!-- {% /added %} -->
<!-- {% /stepCode %} -->
<!-- {% /step %}-->

<!-- {% step %} -->
<!-- {% instructions %} -->
## Run the server

The `cli.run_app()` function starts the agent server. It manages the worker lifecycle, connects to LiveKit, and processes incoming jobs. When you run the script, it listens for incoming calls and automatically spawns agent sessions when calls arrive.
<!-- {% /instructions %} -->

<!-- {% stepCode %} -->
```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, AgentServer, cli, inference
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("answer-call")
logger.setLevel(logging.INFO)

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

class SimpleAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent.
            """
        )

    async def on_enter(self):
        self.session.generate_reply()

@server.rtc_session()
async def my_agent(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )
    agent = SimpleAgent()

    await session.start(agent=agent, room=ctx.room)
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

Run the agent using the `console` command, which starts the agent in console mode. This mode is useful for testing and debugging. It connects to a mocked LiveKit room so you can test the agent locally before deploying. This will not work for real phone calls (since the room is mocked), but it's a great way to quickly test that your agent works.

```bash
python answer_call.py console
```

If you want to test your agent with a real phone call, you'll need to start it in dev mode instead. This will connect your agent to a LiveKit server, which makes it available to your dispatch rules.

```bash
python answer_call.py dev
```

## How inbound calls connect

1. An inbound call hits your LiveKit number.
1. The dispatch rule attaches the SIP participant to your room.
1. If the worker is running, the agent is already in the room and responds immediately—no special SIP handling needed.

## Complete code for the call answering agent

```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, AgentServer, cli, inference
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("answer-call")
logger.setLevel(logging.INFO)

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

class SimpleAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent.
            """
        )

    async def on_enter(self):
        self.session.generate_reply()


@server.rtc_session()
async def my_agent(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )
    agent = SimpleAgent()

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
```
