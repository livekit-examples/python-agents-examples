---
title: Playing Audio
category: basics
tags: [audio, openai, deepgram]
difficulty: beginner
description: Shows how to play audio from a file in an agent.
demonstrates:
  - Playing audio from a file
---

This example shows how to play audio from a file in an agent.

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
python playing_audio.py console
```

## How it works

- Playing audio from a file

## Full example

```python
import logging
from pathlib import Path
import wave
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, Agent, AgentSession, inference, RunContext, function_tool
from livekit.plugins import silero
from livekit import rtc

logger = logging.getLogger("playing-audio")
logger.setLevel(logging.INFO)

load_dotenv(dotenv_path=Path(__file__).parents[3] / '.env')

class AudioPlayerAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice. Don't use any unpronouncable characters.
                If asked to play audio, use the `play_audio_file` function.
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

    @function_tool
    async def play_audio_file(self, context: RunContext):
        audio_path = Path(__file__).parent / "audio.wav"

        with wave.open(str(audio_path), 'rb') as wav_file:
            num_channels = wav_file.getnchannels()
            sample_rate = wav_file.getframerate()
            frames = wav_file.readframes(wav_file.getnframes())

        audio_frame = rtc.AudioFrame(
            data=frames,
            sample_rate=sample_rate,
            num_channels=num_channels,
            samples_per_channel=wav_file.getnframes()
        )

        async def audio_generator():
            yield audio_frame

        await self.session.say("Playing audio file", audio=audio_generator())

        return None, "I've played the audio file for you."

    async def on_enter(self):
        self.session.generate_reply()

async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=AudioPlayerAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
```
