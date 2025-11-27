---
title: Interrupt User
category: basics
tags: [interrupts, openai, deepgram]
difficulty: beginner
description: Shows how to interrupt the user if they try to say more than one sentence.
demonstrates:
  - Using the `stt_node` to read the user's input in real time
  - Setting `allow_interruptions` to `False` to prevent the user from interrupting the agent
---

This example shows how to interrupt the user if they try to say more than one sentence.

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
python interrupts_user.py console
```

## How it works

- Using the `stt_node` to read the user's input in real time
- Setting `allow_interruptions` to `False` to prevent the user from interrupting the agent

## Full example

```python
from pathlib import Path
from typing import AsyncIterable, Optional
import re
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, Agent, AgentSession
from livekit.plugins import silero
from livekit import rtc

load_dotenv(dotenv_path=Path(__file__).parents[3] / '.env')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InterruptUserAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice who will interrupt the user if they try to say more than one sentence.
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
            vad=silero.VAD.load(),
            allow_interruptions=False
        )
        self.text_buffer = ""

    async def stt_node(self, text: AsyncIterable[str], model_settings: Optional[dict] = None) -> Optional[AsyncIterable[rtc.AudioFrame]]:
        parent_stream = super().stt_node(text, model_settings)

        if parent_stream is None:
            return None

        async def replay_user_input(text: str):
            await self.session.say("Let me stop you there, and respond. You said: " + text)

        async def process_stream():
            async for event in parent_stream:
                if hasattr(event, 'type') and str(event.type) == "SpeechEventType.FINAL_TRANSCRIPT" and event.alternatives:
                    transcript = event.alternatives[0].text

                    self.text_buffer += " " + transcript
                    self.text_buffer = self.text_buffer.strip()

                    sentence_pattern = r'[.!?]+'
                    if re.search(sentence_pattern, self.text_buffer):
                        sentences = re.split(sentence_pattern, self.text_buffer)

                        if len(sentences) > 1:
                            for i in range(len(sentences) - 1):
                                if sentences[i].strip():
                                    logger.info(f"Complete sentence detected: '{sentences[i].strip()}'")
                                    await replay_user_input(sentences[i].strip())

                            self.text_buffer = sentences[-1].strip()

                yield event

        return process_stream()

    async def on_enter(self):
        self.session.say("I'll interrupt you after 1 sentence.")

async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=InterruptUserAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
```
