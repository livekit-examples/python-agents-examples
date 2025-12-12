---
title: Interrupt User
category: pipeline-llm
tags: [pipeline-llm, openai, deepgram]
difficulty: intermediate
description: Shows how to interrupt the user if they've spoken too much.
demonstrates:
  - Using the `session.say` method to interrupt the user.
  - Using the `allow_interruptions` parameter to prevent the user from interrupting the agent.
  - Once the agent has spoken, it will allow the user to interrupt again.
---

In this recipe you will interrupt a user who keeps talking. The agent counts sentences in the live transcript; when the buffer gets too long, it cuts in with `session.say` and disables interruptions for its response.

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

Load environment variables and configure logging for transcript debugging. We also initialize the `AgentServer`.

```python
import logging
import asyncio
import re
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, cli, Agent, AgentSession, AgentServer
from livekit.plugins import openai, deepgram, silero
from livekit.agents.llm import ChatContext, ChatMessage

load_dotenv()

logger = logging.getLogger("interrupt-user")
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
        stt=deepgram.STT(),
        llm=openai.LLM(),
        tts=openai.TTS(),
        vad=ctx.proc.userdata["vad"],
    )
    agent = Agent(
        instructions="You are a helpful agent that politely interrupts users when they talk too much.",
    )
    # ...
```

## Count sentences in streaming transcripts

Maintain a rolling transcript buffer from `user_input_transcribed` events. Ignore finals for counting; when the buffer exceeds the sentence limit, trigger an interruption.

```python
    def count_sentences(text):
        """Count the number of sentences in text"""
        sentences = re.findall(r'[^.!?]+[.!?](?:\s|$)', text)
        return len(sentences)
        
    transcript_buffer = ""
    max_sentences = 3

    @session.on("user_input_transcribed")
    def on_transcript(transcript):
        nonlocal transcript_buffer

        if transcript.is_final:
            logger.info(f"Received final transcript: {transcript.transcript}")
            return

        transcript_buffer += " " + transcript.transcript
        transcript_buffer = transcript_buffer.strip()

        if count_sentences(transcript_buffer) >= max_sentences:
            asyncio.create_task(handle_interruption(...))
            transcript_buffer = ""
```

## Interrupt with a focused prompt

Build a temporary `ChatContext` that summarizes what the user said and asks the LLM to redirect the conversation. Use `session.say(..., allow_interruptions=False)` so the user cannot talk over the interruption.

```python
    async def handle_interruption(context):
        await agent.update_chat_ctx(context)
        session.say("Sorry, can I pause you there?", allow_interruptions=False)
        await session.generate_reply(allow_interruptions=False)
```

```python
            interruption_ctx = ChatContext([
                ChatMessage(
                    type="message",
                    role="system",
                    content=["You are an agent that politely interrupts users who speak too much. Create a brief response that acknowledges what they've said so far, then redirects to get more focused information."]
                ),
                ChatMessage(type="message", role="user", content=[f"User has been speaking and said: {transcript_buffer}"])
            ])
```

## Reset on session start and start the session

Clear the buffer when the session starts, generate an opening reply, and launch the agent.

```python
    @session.on("session_start")
    def on_session_start():
        nonlocal transcript_buffer
        transcript_buffer = ""
        session.generate_reply()

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()
```

## Run it

Run the agent using the `console` command, which starts the agent in console mode.

```bash
python interrupt_user.py console
```

## How it works

1. Streamed transcripts are buffered and counted per sentence.
2. When the buffer hits the threshold, the agent builds a focused prompt and interrupts via `session.say`.
3. `allow_interruptions=False` keeps the interruption audible; it is re-enabled for subsequent turns.
4. The buffer resets after each interruption so counting starts fresh.

## Full example

```python
import logging
import asyncio
import re
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, cli, Agent, AgentSession, AgentServer
from livekit.plugins import openai, deepgram, silero
from livekit.agents.llm import ChatContext, ChatMessage

load_dotenv()

logger = logging.getLogger("interrupt-user")
logger.setLevel(logging.INFO)

def count_sentences(text):
    """Count the number of sentences in text"""
    sentences = re.findall(r'[^.!?]+[.!?](?:\s|$)', text)
    return len(sentences)

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session()
async def entrypoint(ctx: JobContext):
    session = AgentSession(
        stt=deepgram.STT(),
        llm=openai.LLM(),
        tts=openai.TTS(),
        vad=ctx.proc.userdata["vad"],
    )
    agent = Agent(
        instructions="You are a helpful agent that politely interrupts users when they talk too much.",
    )

    async def handle_interruption(context):
        await agent.update_chat_ctx(context)
        session.say("Sorry, can I pause you there?", allow_interruptions=False)
        await session.generate_reply(allow_interruptions=False)

    transcript_buffer = ""
    max_sentences = 3

    @session.on("user_input_transcribed")
    def on_transcript(transcript):
        nonlocal transcript_buffer

        if transcript.is_final:
            logger.info(f"Received final transcript: {transcript.transcript}")
            return

        transcript_buffer += " " + transcript.transcript
        transcript_buffer = transcript_buffer.strip()

        logger.info(f"Buffer: {transcript_buffer}")

        sentence_count = count_sentences(transcript_buffer)
        logger.info(f"Sentence count: {sentence_count}")

        if sentence_count >= max_sentences:
            logger.info("Interrupting user...")

            interruption_ctx = ChatContext([
                ChatMessage(
                    type="message",
                    role="system",
                    content=["You are an agent that politely interrupts users who speak too much. Create a brief response that acknowledges what they've said so far, then redirects to get more focused information."]
                ),
                ChatMessage(type="message", role="user", content=[f"User has been speaking and said: {transcript_buffer}"])
            ])

            asyncio.create_task(handle_interruption(interruption_ctx))
            transcript_buffer = ""

    @session.on("session_start")
    def on_session_start():
        nonlocal transcript_buffer
        transcript_buffer = ""
        session.generate_reply()

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
```
