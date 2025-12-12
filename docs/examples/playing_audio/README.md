---
title: Playing Audio
category: basics
tags: [audio, deepgram, openai, cartesia]
difficulty: beginner
description: Shows how to play audio from a file in an agent.
demonstrates:
  - Playing audio from a file
---

This example shows how to expose a function tool that plays a local WAV file into the call. The agent reads the file, wraps it in an audio frame, and streams it via `session.say`.

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
- Place an `audio.wav` file in the same directory as the script

## Load environment, logging, and define an AgentServer

Load environment variables, configure logging, and initialize the AgentServer.

```python
import logging
from pathlib import Path
import wave
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession, inference, RunContext, function_tool
from livekit.plugins import silero
from livekit import rtc

load_dotenv()

logger = logging.getLogger("playing-audio")
logger.setLevel(logging.INFO)

server = AgentServer()
```

## Define the agent with audio playback tool

Create a lightweight agent with instructions and a function tool that reads a WAV file, builds an `AudioFrame`, and streams it to the user.

```python
class AudioPlayerAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice. Don't use any unpronouncable characters.
                If asked to play audio, use the `play_audio_file` function.
            """
        )

    @function_tool
    async def play_audio_file(self, context: RunContext):
        """Play a local audio file"""
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
```

## Prewarm VAD for faster connections

Preload the VAD model once per process to reduce connection latency.

```python
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm
```

## Define the rtc session entrypoint

Create the session with STT/LLM/TTS configuration and start the audio player agent.

```python
@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-5-mini"),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(agent=AudioPlayerAgent(), room=ctx.room)
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
python playing_audio.py console
```

## How it works

1. The agent greets the user on entry.
2. The LLM can invoke `play_audio_file` when asked to play audio.
3. The tool reads a local WAV file, wraps it in an `AudioFrame`, and streams it via `session.say`.
4. A short spoken preamble ("Playing audio file") plays before the audio clip.
5. The rest of the media pipeline continues unchanged.

## Full example

```python
import logging
from pathlib import Path
import wave
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession, inference, RunContext, function_tool
from livekit.plugins import silero
from livekit import rtc

load_dotenv()

logger = logging.getLogger("playing-audio")
logger.setLevel(logging.INFO)

class AudioPlayerAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice. Don't use any unpronouncable characters.
                If asked to play audio, use the `play_audio_file` function.
            """
        )

    @function_tool
    async def play_audio_file(self, context: RunContext):
        """Play a local audio file"""
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
        preemptive_generation=True,
    )

    await session.start(agent=AudioPlayerAgent(), room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
```
