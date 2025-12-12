---
title: Gemini Realtime Agent with Live Vision
category: realtime
tags: [gemini_realtime, live_vision, google]
difficulty: beginner
description: Minimal Gemini Realtime model agent setup with live vision capabilities
demonstrates:
  - Gemini Realtime model basic usage
  - Live vision capabilities
  - Session-based generation
  - VAD with Silero
style: two-column
---

This example demonstrates how to start a Gemini Realtime agent that can see video from the call. The session uses Google's realtime model with proactivity enabled and Silero VAD for turn-taking.

## Prerequisites

- Add a `.env` in this directory with your LiveKit and Google credentials:
  ```
  LIVEKIT_URL=your_livekit_url
  LIVEKIT_API_KEY=your_api_key
  LIVEKIT_API_SECRET=your_api_secret
  GOOGLE_API_KEY=your_google_api_key
  ```
- Install dependencies:
  ```bash
  pip install "livekit-agents[silero,google]" python-dotenv
  ```

<!-- {% step %} -->
<!-- {% instructions %} -->
## Load environment, logging, and define an AgentServer

Start by importing the required modules and setting up logging. The `AgentServer` wraps your application and manages the worker lifecycle.
<!-- {% /instructions %} -->

<!-- {% stepCode %} -->
```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, AgentServer, cli, RoomInputOptions
from livekit.plugins import silero, google

load_dotenv()

logger = logging.getLogger("gemini-live-vision")
logger.setLevel(logging.INFO)

server = AgentServer()
```
<!-- {% /stepCode %} -->
<!-- {% /step %}-->

<!-- {% step %} -->
<!-- {% instructions %} -->
## Prewarm VAD for faster connections

Preload the VAD model once per process. This runs before any sessions start and stores the VAD instance in `proc.userdata` so it can be reused, cutting down on connection latency.
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
## Create a simple vision-capable agent

Keep the agent minimal—just add instructions that acknowledge its vision capabilities. The actual video processing comes from the session configuration with `RoomInputOptions`.
<!-- {% /instructions %} -->

<!-- {% stepCode %} -->
```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, AgentServer, cli, RoomInputOptions
from livekit.plugins import silero, google

load_dotenv()

logger = logging.getLogger("gemini-live-vision")
logger.setLevel(logging.INFO)

server = AgentServer()
```
<!-- {% added %} -->
```python
class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="You are a helpful voice AI assistant that can see the world around you.")
```
<!-- {% /added %} -->
<!-- {% /stepCode %} -->
<!-- {% /step %}-->

<!-- {% step %} -->
<!-- {% instructions %} -->
## Define the RTC session entrypoint

Configure the Gemini Realtime model with proactivity and affective dialog enabled. Proactivity lets the model speak when it has something relevant to say. Enable video in `RoomInputOptions` so the agent receives video frames from the room. After starting and connecting, call `generate_reply()` to have the agent greet the caller.
<!-- {% /instructions %} -->

<!-- {% stepCode %} -->
```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, AgentServer, cli, RoomInputOptions
from livekit.plugins import silero, google

load_dotenv()

logger = logging.getLogger("gemini-live-vision")
logger.setLevel(logging.INFO)

server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="You are a helpful voice AI assistant that can see the world around you.")
```
<!-- {% added %} -->
```python
@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        llm=google.beta.realtime.RealtimeModel(
            model="gemini-2.5-flash-native-audio-preview-09-2025",
            proactivity=True,
            enable_affective_dialog=True
        ),
        vad=ctx.proc.userdata["vad"],
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(video_enabled=True),
    )
    await ctx.connect()

    await session.generate_reply()
```
<!-- {% /added %} -->
<!-- {% /stepCode %} -->
<!-- {% /step %}-->

<!-- {% step %} -->
<!-- {% instructions %} -->
## Run the server

The `cli.run_app()` function starts the agent server and manages connections to LiveKit.
<!-- {% /instructions %} -->

<!-- {% stepCode %} -->
```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, AgentServer, cli, RoomInputOptions
from livekit.plugins import silero, google

load_dotenv()

logger = logging.getLogger("gemini-live-vision")
logger.setLevel(logging.INFO)

server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="You are a helpful voice AI assistant that can see the world around you.")


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        llm=google.beta.realtime.RealtimeModel(
            model="gemini-2.5-flash-native-audio-preview-09-2025",
            proactivity=True,
            enable_affective_dialog=True
        ),
        vad=ctx.proc.userdata["vad"],
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(video_enabled=True),
    )
    await ctx.connect()

    await session.generate_reply()
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

```bash
python gemini_live_vision.py console
```

## How it works

1. The session uses Gemini Realtime as the LLM with proactivity turned on.
2. `RoomInputOptions(video_enabled=True)` lets the agent receive video frames.
3. Silero VAD manages turn-taking for audio.
4. An initial `generate_reply()` greets the caller; the model can incorporate vision context in responses.

## Full example

```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, AgentServer, cli, RoomInputOptions
from livekit.plugins import silero, google

load_dotenv()

logger = logging.getLogger("gemini-live-vision")
logger.setLevel(logging.INFO)


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="You are a helpful voice AI assistant that can see the world around you.")


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        llm=google.beta.realtime.RealtimeModel(
            model="gemini-2.5-flash-native-audio-preview-09-2025",
            proactivity=True,
            enable_affective_dialog=True
        ),
        vad=ctx.proc.userdata["vad"],
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(video_enabled=True),
    )
    await ctx.connect()

    await session.generate_reply()


if __name__ == "__main__":
    cli.run_app(server)
```
