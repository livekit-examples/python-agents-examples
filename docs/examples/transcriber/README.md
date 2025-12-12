---
title: Transcriber
category: pipeline-stt
tags: [pipeline-stt, deepgram]
difficulty: beginner
description: Shows how to transcribe user speech to text without TTS or an LLM.
demonstrates:
  - Saving transcripts to a file.
  - An Agent that does not have TTS or an LLM. This is STT only.
---

This example builds a minimal STT-only agent that listens to the caller and appends each final transcript to a log file with timestamps. There is no LLM or TTS pipeline—just speech-to-text and a file writer.

## Prerequisites

- A `.env` at the repo root with your LiveKit credentials:
  ```
  LIVEKIT_URL=your_livekit_url
  LIVEKIT_API_KEY=your_api_key
  LIVEKIT_API_SECRET=your_api_secret
  ```
- Install dependencies:
  ```bash
  pip install python-dotenv "livekit-agents[silero]"
  ```

## Load configuration and create the AgentServer

Import the necessary modules and load environment variables. Create an AgentServer to handle incoming sessions.

```python
import datetime
from dotenv import load_dotenv
from livekit.agents import JobContext, AgentServer, cli, Agent, AgentSession, inference

load_dotenv()

server = AgentServer()
```

## Create an STT-only agent session

Start an AgentSession with only STT configured. The Agent is lightweight with just instructions—no TTS or LLM needed for pure transcription.

```python
session = AgentSession(
    stt=inference.STT(model="deepgram/nova-3-general"),
)

await session.start(
    agent=Agent(instructions="You are a helpful assistant that transcribes user speech to text."),
    room=ctx.room
)
```

## Listen for final transcripts

Subscribe to `user_input_transcribed` and append each final transcript to `user_speech_log.txt` with a timestamp.

```python
@session.on("user_input_transcribed")
def on_transcript(transcript):
    if transcript.is_final:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("user_speech_log.txt", "a") as f:
            f.write(f"[{timestamp}] {transcript.transcript}\n")
```

## Create the RTC session entrypoint

Wire it all together in the entrypoint so the agent begins listening immediately when the session starts.

```python
@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
    )

    @session.on("user_input_transcribed")
    def on_transcript(transcript):
        if transcript.is_final:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("user_speech_log.txt", "a") as f:
                f.write(f"[{timestamp}] {transcript.transcript}\n")

    await session.start(
        agent=Agent(instructions="You are a helpful assistant that transcribes user speech to text."),
        room=ctx.room
    )
    await ctx.connect()
```

## Run it

```console
python transcriber.py console
```

The agent starts listening right away and logs transcriptions to `user_speech_log.txt`.

## How it works

1. Deepgram STT streams audio and emits `user_input_transcribed` events.
2. Each final transcript is timestamped and appended to a log file.
3. Because there is no LLM/TTS, the agent never speaks; it only records.
4. The rest of the session lifecycle is handled by AgentSession.

## Log file format

```
[2024-01-15 14:30:45] Hello, this is my first transcription
[2024-01-15 14:30:52] Testing the speech to text functionality
```

## Full example

```python
import datetime
from dotenv import load_dotenv
from livekit.agents import JobContext, AgentServer, cli, Agent, AgentSession, inference

load_dotenv()

server = AgentServer()

@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
    )

    @session.on("user_input_transcribed")
    def on_transcript(transcript):
        if transcript.is_final:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("user_speech_log.txt", "a") as f:
                f.write(f"[{timestamp}] {transcript.transcript}\n")

    await session.start(
        agent=Agent(instructions="You are a helpful assistant that transcribes user speech to text."),
        room=ctx.room
    )
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
```
