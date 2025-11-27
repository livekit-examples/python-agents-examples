---
title: Keyword Detection
category: pipeline-stt
tags: [pipeline-stt, assemblyai, openai, cartesia]
difficulty: intermediate
description: Shows how to detect keywords in user speech.
demonstrates:
  - If the user says a keyword, the agent will log the keyword to the console.
  - Using the `stt_node` method to override the default STT node and add custom logic to detect keywords.
---

In this example, you will build a voice agent that listens for specific keywords while keeping the usual LLM conversation
running. The agent overrides the STT pipeline so it can scan transcripts before they reach the LLM.

## Prerequisites

- A `.env` file with LiveKit credentials.
- The agents framework, the Silero VAD plugin, and `dotenv` installed via `pip install 'livekit-agents[silero]' dotenv`

## Setting up the environment

Load environment variables and configure logging:

```python
import logging
from typing import AsyncIterable, Optional
from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import JobContext, WorkerOptions, cli, Agent, AgentSession
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("keyword-detection")
logger.setLevel(logging.INFO)
```

## Creating the keyword-aware agent

Define the agent using LiveKit Inference so that we don't need any API keys for external providers. In this case we're using AssemblyAI for STT, OpenAI
for the LLM, and Cartesia for TTS:

```python
class KeywordDetectionAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent that detects keywords in user speech.
            """,
            stt=inference.STT(
                model="assemblyai/universal-streaming",
                language="en"
            ),
            llm=inference.LLM(
                model="openai/gpt-5-mini",
                provider="openai",
            ),
            tts=inference.TTS(
                model="cartesia/sonic-3",
                voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
            ),
            vad=silero.VAD.load()
        )

    async def on_enter(self):
        self.session.generate_reply()
```

## Watching transcripts for keywords

Override `stt_node` to inspect the transcript stream. Only final transcripts trigger detection so partial results do not
spam the logs:

```python
    async def stt_node(self, text: AsyncIterable[str], model_settings: Optional[dict] = None) -> Optional[AsyncIterable[rtc.AudioFrame]]:
        keywords = ["Shane", "hello", "thanks", "bye"]
        parent_stream = super().stt_node(text, model_settings)

        if parent_stream is None:
            return None

        async def process_stream():
            async for event in parent_stream:
                if hasattr(event, 'type') and str(event.type) == "SpeechEventType.FINAL_TRANSCRIPT" and event.alternatives:
                    transcript = event.alternatives[0].text

                    for keyword in keywords:
                        if keyword.lower() in transcript.lower():
                            logger.info(f"Keyword detected: '{keyword}'")

                yield event

        return process_stream()
```

## Starting the session

Create a simple entrypoint that starts the agent in the connected room:

```python
async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=KeywordDetectionAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
```

## Running the agent

```bash
python keyword_detection.py console
```

Speak words like "hello", "thanks", or "bye" and watch the logs for keyword detections.

## How it works

1. The agent starts with a greeting by calling `generate_reply`.
2. Incoming audio is transcribed by the configured STT inference string.
3. Final transcripts are scanned for keywords; matches are logged.
4. All events continue to flow to the base agent so the conversation stays natural.

For a complete working example, see the code below:

```python
import logging
from pathlib import Path
from typing import AsyncIterable, Optional
from dotenv import load_dotenv
from livekit import rtc
from livekit.plugins import silero

load_dotenv(dotenv_path=Path(__file__).parents[3] / '.env')

logger = logging.getLogger("keyword-detection")
logger.setLevel(logging.INFO)

class KeywordDetectionAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent that detects keywords in user speech.
            """,
            stt=inference.STT(
                model="assemblyai/universal-streaming",
                language="en"
            ),
            llm=inference.LLM(
                model="openai/gpt-5-mini",
                provider="openai",
            ),
            tts=inference.TTS(
                model="cartesia/sonic-3",
                voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
            ),
            vad=silero.VAD.load()
        )

    async def on_enter(self):
        self.session.generate_reply()

    async def stt_node(self, text: AsyncIterable[str], model_settings: Optional[dict] = None) -> Optional[AsyncIterable[rtc.AudioFrame]]:
        keywords = ["Shane", "hello", "thanks", "bye"]
        parent_stream = super().stt_node(text, model_settings)

        if parent_stream is None:
            return None

        async def process_stream():
            async for event in parent_stream:
                if hasattr(event, 'type') and str(event.type) == "SpeechEventType.FINAL_TRANSCRIPT" and event.alternatives:
                    transcript = event.alternatives[0].text

                    for keyword in keywords:
                        if keyword.lower() in transcript.lower():
                            logger.info(f"Keyword detected: '{keyword}'")

                yield event

        return process_stream()

async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=KeywordDetectionAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
```
