---
title: Keyword Detection
category: pipeline-stt
tags: [pipeline-stt, deepgram, openai, cartesia]
difficulty: intermediate
description: Shows how to detect keywords in user speech.
demonstrates:
  - If the user says a keyword, the agent will log the keyword to the console.
  - Using the `user_input_transcribed` event to inspect transcripts.
---

In this example, you will build a voice agent that listens for specific keywords while keeping the usual LLM conversation running. The agent listens to transcription events to scan transcripts before the conversation continues.

## Prerequisites

- A `.env` file with LiveKit credentials.
- The agents framework, the Silero VAD plugin, and `dotenv` installed via `pip install 'livekit-agents[silero]' dotenv`

## Setting up the environment

Load environment variables and configure logging:

```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, cli, Agent, AgentSession, AgentServer, inference
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("keyword-detection")
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
        instructions="You are a helpful agent that detects keywords in user speech.",
    )
    # ...
```

## Watching transcripts for keywords

Listen to the `user_input_transcribed` event to inspect the transcript stream. Only final transcripts trigger detection so partial results do not spam the logs:

```python
    keywords = ["Shane", "hello", "thanks", "bye"]

    @session.on("user_input_transcribed")
    def on_transcript(transcript):
        if transcript.is_final:
            text = transcript.transcript
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    logger.info(f"Keyword detected: '{keyword}'")
```

## Starting the session

Start the session and connect to the room:

```python
    @session.on("session_start")
    def on_session_start():
        session.generate_reply()

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
```

## Running the agent

```bash
python keyword_detection.py console
```

Speak words like "hello", "thanks", or "bye" and watch the logs for keyword detections.

## How it works

1. The agent starts with a greeting by calling `generate_reply`.
2. Incoming audio is transcribed by the configured STT.
3. Final transcripts are scanned for keywords; matches are logged.
4. The conversation continues naturally.

## Full example

```python
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, cli, Agent, AgentSession, AgentServer, inference
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("keyword-detection")
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
        instructions="You are a helpful agent that detects keywords in user speech.",
    )

    keywords = ["Shane", "hello", "thanks", "bye"]

    @session.on("user_input_transcribed")
    def on_transcript(transcript):
        if transcript.is_final:
            text = transcript.transcript
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    logger.info(f"Keyword detected: '{keyword}'")

    @session.on("session_start")
    def on_session_start():
        session.generate_reply()

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
```
