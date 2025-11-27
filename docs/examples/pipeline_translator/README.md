---
title: Pipeline Translator Agent
category: translation
tags: [translation, multilingual, french, elevenlabs, direct-translation]
difficulty: intermediate
description: Simple translation pipeline that converts English speech to French
demonstrates:
  - Direct language translation workflow
  - Multilingual TTS configuration with ElevenLabs
  - Simple translation-focused agent instructions
  - Clean input-to-output translation pipeline
  - Voice-to-voice translation system
---

This example Simple translation pipeline that converts English speech to French.

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

## Run it

```bash
python pipeline_translator.py console
```

## How it works

- Direct language translation workflow
- Multilingual TTS configuration with ElevenLabs
- Simple translation-focused agent instructions
- Clean input-to-output translation pipeline
- Voice-to-voice translation system

## Full example

```python
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, Agent, AgentSession
from livekit.plugins import openai, silero, deepgram, elevenlabs

load_dotenv(dotenv_path=Path(__file__).parents[3] / '.env')

logger = logging.getLogger("pipeline-translator")
logger.setLevel(logging.INFO)

class SimpleAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a translator. You translate the user's speech from English to French.
                Every message you receive, translate it directly into French.
                Do not respond with anything else but the translation.
            """,
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o"),
            tts=elevenlabs.TTS(
                model="eleven_multilingual_v2"
            ),
            vad=silero.VAD.load()
        )
    
    async def on_enter(self):
        self.session.generate_reply()

async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=SimpleAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
```
