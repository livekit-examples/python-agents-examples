---
title: Repeater
category: basics
tags: [repeater, deepgram, openai, cartesia]
difficulty: beginner
description: Shows how to create an agent that can repeat what the user says.
demonstrates:
  - Using the `on_user_input_transcribed` event to listen to the user's input
  - Using the `say` method to respond to the user with the same input
---

This example shows how to build a simple repeater: when the user finishes speaking, the agent says back exactly what it heard by listening to the `user_input_transcribed` event.

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

## Load environment and define an AgentServer

Load your `.env` so the media plugins can authenticate and initialize the AgentServer.

```python
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession, inference
from livekit.plugins import silero

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

## Define the rtc session with transcript handler

Create the session with interruptions disabled so playback is not cut off mid-echo. Attach a handler to `user_input_transcribed`; once a transcript is marked final, echo it back with `session.say`.

```python
@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-5-mini"),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
        allow_interruptions=False,
    )

    @session.on("user_input_transcribed")
    def on_transcript(transcript):
        if transcript.is_final:
            session.say(transcript.transcript)

    await session.start(
        agent=Agent(
            instructions="You are a helpful assistant that repeats what the user says."
        ),
        room=ctx.room
    )
    await ctx.connect()
```

## Run the server

Start the agent server with the CLI runner.

```python
if __name__ == "__main__":
    cli.run_app(server)
```

## Run it

```bash
python repeater.py console
```

## How it works

1. The VAD is prewarmed once per process for faster connections.
2. A session-level event emits transcripts as the user speaks.
3. When the transcript is final, the handler calls `session.say` with the same text.
4. Because interruptions are disabled, the echoed audio plays fully.
5. This pattern is a starting point for building more advanced post-processing on transcripts.

## Full example

```python
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession, inference
from livekit.plugins import silero

load_dotenv()

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-5-mini"),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
        allow_interruptions=False,
    )

    @session.on("user_input_transcribed")
    def on_transcript(transcript):
        if transcript.is_final:
            session.say(transcript.transcript)

    await session.start(
        agent=Agent(
            instructions="You are a helpful assistant that repeats what the user says."
        ),
        room=ctx.room
    )
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
```
