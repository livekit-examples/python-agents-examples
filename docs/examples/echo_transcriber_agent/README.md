---
title: Echo Transcriber Agent
category: basics
tags: [echo, transcriber, deepgram, silero]
difficulty: beginner
description: Shows how to create an agent that can transcribe audio and echo it back.
demonstrates:
  - Transcribing audio
  - Echoing audio back that's stored in a buffer
  - Custom STT node processing
  - Custom VAD stream handling
---

This example demonstrates how to build an echo agent that listens to the caller, buffers their audio, and plays it back once they stop speaking. It taps into the STT pipeline and uses a custom VAD loop to detect when to echo.

## Prerequisites

- Add a `.env` in this directory with your LiveKit credentials:
  ```
  LIVEKIT_URL=your_livekit_url
  LIVEKIT_API_KEY=your_api_key
  LIVEKIT_API_SECRET=your_api_secret
  ```
- Install dependencies:
  ```bash
  pip install "livekit-agents[silero,noise-cancellation]" python-dotenv
  ```

## Load environment, logging, and define an AgentServer

Start by importing the required modules and setting up logging. The `AgentServer` wraps your application and manages the worker lifecycle.

```python
import logging
import asyncio
from typing import AsyncIterable, Optional
from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, AgentServer, cli
from livekit.agents.voice import room_io
from livekit.agents.vad import VADEventType
from livekit.plugins import silero, noise_cancellation

load_dotenv()

logger = logging.getLogger("echo-transcriber")
logger.setLevel(logging.INFO)

server = AgentServer()
```

## Define the echo transcriber agent

Create an agent that disables the default TTS greeting and initializes buffering state. The agent uses a custom Silero VAD stream to detect speech boundaries independently from the session's VAD. This gives you fine-grained control over when to start and stop buffering audio.

```python
class EchoTranscriberAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="You are an echo transcriber that listens and repeats audio.",
            stt="deepgram/nova-3-general",
            vad=None,
            allow_interruptions=False
        )

        self.audio_source = None
        self.echo_track = None
        self.ctx = None
        self.audio_buffer = []
        self.custom_vad = silero.VAD.load(
            min_speech_duration=0.2,
            min_silence_duration=0.6,
        )
        self.vad_stream = self.custom_vad.stream()
        self.is_speaking = False
        self.is_echoing = False
        self.audio_format_set = False

    async def on_enter(self):
        pass  # suppress the default greeting

    def set_context(self, ctx: JobContext):
        self.ctx = ctx
```

## Publish an echo track on demand

When the first audio frame arrives, create a local audio track and publish it to the room. This track will be used to play back the buffered audio.

```python
    async def setup_audio_output(self):
        if self.audio_format_set:
            return

        self.audio_source = rtc.AudioSource(sample_rate=48000, num_channels=1)
        self.echo_track = rtc.LocalAudioTrack.create_audio_track("echo", self.audio_source)
        await self.ctx.room.local_participant.publish_track(
            self.echo_track,
            rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE),
        )
        self.audio_format_set = True
```

## Tap into the STT node to buffer audio

Override the `stt_node` method to wrap the audio stream. This lets you push each frame through your custom VAD, store it in a rolling buffer, and still pass frames unchanged to the STT for transcription.

```python
    async def stt_node(self, audio: AsyncIterable[rtc.AudioFrame], model_settings: Optional[dict] = None) -> Optional[AsyncIterable[str]]:
        async def audio_with_buffer():
            first_frame = True
            async for frame in audio:
                if first_frame:
                    await self.setup_audio_output()
                    first_frame = False

                if not self.is_echoing:
                    self.vad_stream.push_frame(frame)
                    self.audio_buffer.append(frame)
                    if len(self.audio_buffer) > 1000:
                        self.audio_buffer.pop(0)

                yield frame

        return super().stt_node(audio_with_buffer(), model_settings)
```

## Define the RTC session entrypoint with VAD processing

The entrypoint sets room attributes for UI state, subscribes to transcription events, and runs a background task that processes VAD events. When speech ends, it copies the buffer and plays back each frame through the audio source.

```python
@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    await ctx.room.local_participant.set_attributes({"lk.agent.state": "listening"})

    session = AgentSession()
    agent = EchoTranscriberAgent()
    agent.set_context(ctx)

    @session.on("user_input_transcribed")
    def on_transcript(transcript):
        if transcript.is_final:
            logger.info(f"Transcribed: {transcript.transcript}")

    async def process_vad():
        async for vad_event in agent.vad_stream:
            if agent.is_echoing:
                continue

            if vad_event.type == VADEventType.START_OF_SPEECH:
                agent.is_speaking = True
                if len(agent.audio_buffer) > 100:
                    agent.audio_buffer = agent.audio_buffer[-100:]

            elif vad_event.type == VADEventType.END_OF_SPEECH:
                agent.is_speaking = False
                agent.is_echoing = True

                await ctx.room.local_participant.set_attributes({"lk.agent.state": "speaking"})

                frames_to_play = agent.audio_buffer.copy()
                agent.audio_buffer.clear()

                if agent.audio_source:
                    for frame in frames_to_play:
                        await agent.audio_source.capture_frame(frame)

                agent.is_echoing = False
                await ctx.room.local_participant.set_attributes({"lk.agent.state": "listening"})

    vad_task = asyncio.create_task(process_vad())

    await session.start(
        agent=agent,
        room=ctx.room,
        room_input_options=room_io.RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
            audio_sample_rate=48000,
            audio_num_channels=1,
        )
    )
    await ctx.connect()

    await vad_task
```

## Run the server

The `cli.run_app()` function starts the agent server and manages connections to LiveKit.

```python
if __name__ == "__main__":
    cli.run_app(server)
```

## Run it

```bash
python echo_transcriber_agent.py console
```

## How it works

1. Custom VAD detects when speech starts and ends.
2. The STT node is wrapped to both buffer raw audio and pass frames to transcription.
3. After speech ends, buffered audio is published back into the room as an echo track.
4. Room attributes show listening/speaking state so a UI can react.

## Full example

```python
import logging
import asyncio
from typing import AsyncIterable, Optional
from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import JobContext, JobProcess, Agent, AgentSession, AgentServer, cli
from livekit.agents.voice import room_io
from livekit.agents.vad import VADEventType
from livekit.plugins import silero, noise_cancellation

load_dotenv()

logger = logging.getLogger("echo-transcriber")
logger.setLevel(logging.INFO)


class EchoTranscriberAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="You are an echo transcriber that listens and repeats audio.",
            stt="deepgram/nova-3-general",
            vad=None,
            allow_interruptions=False
        )

        self.audio_source = None
        self.echo_track = None
        self.ctx = None
        self.audio_buffer = []
        self.custom_vad = silero.VAD.load(
            min_speech_duration=0.2,
            min_silence_duration=0.6,
        )
        self.vad_stream = self.custom_vad.stream()
        self.is_speaking = False
        self.is_echoing = False
        self.audio_format_set = False

    async def on_enter(self):
        pass

    def set_context(self, ctx: JobContext):
        self.ctx = ctx

    async def setup_audio_output(self):
        if self.audio_format_set:
            return

        self.audio_source = rtc.AudioSource(sample_rate=48000, num_channels=1)
        self.echo_track = rtc.LocalAudioTrack.create_audio_track("echo", self.audio_source)
        await self.ctx.room.local_participant.publish_track(
            self.echo_track,
            rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE),
        )
        self.audio_format_set = True

    async def stt_node(self, audio: AsyncIterable[rtc.AudioFrame], model_settings: Optional[dict] = None) -> Optional[AsyncIterable[str]]:
        async def audio_with_buffer():
            first_frame = True
            async for frame in audio:
                if first_frame:
                    await self.setup_audio_output()
                    first_frame = False

                if not self.is_echoing:
                    self.vad_stream.push_frame(frame)
                    self.audio_buffer.append(frame)
                    if len(self.audio_buffer) > 1000:
                        self.audio_buffer.pop(0)

                yield frame

        return super().stt_node(audio_with_buffer(), model_settings)


server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    await ctx.room.local_participant.set_attributes({"lk.agent.state": "listening"})

    session = AgentSession()
    agent = EchoTranscriberAgent()
    agent.set_context(ctx)

    @session.on("user_input_transcribed")
    def on_transcript(transcript):
        if transcript.is_final:
            logger.info(f"Transcribed: {transcript.transcript}")

    async def process_vad():
        async for vad_event in agent.vad_stream:
            if agent.is_echoing:
                continue

            if vad_event.type == VADEventType.START_OF_SPEECH:
                agent.is_speaking = True
                logger.info("VAD: Start of speech detected")
                if len(agent.audio_buffer) > 100:
                    agent.audio_buffer = agent.audio_buffer[-100:]

            elif vad_event.type == VADEventType.END_OF_SPEECH:
                agent.is_speaking = False
                agent.is_echoing = True
                buffer_size = len(agent.audio_buffer)
                logger.info(f"VAD: End of speech, echoing {buffer_size} frames")

                await ctx.room.local_participant.set_attributes({"lk.agent.state": "speaking"})

                frames_to_play = agent.audio_buffer.copy()
                agent.audio_buffer.clear()

                if agent.audio_source:
                    for frame in frames_to_play:
                        await agent.audio_source.capture_frame(frame)
                else:
                    logger.error("Audio source not initialized yet")

                agent.is_echoing = False
                logger.info("Finished echoing")

                await ctx.room.local_participant.set_attributes({"lk.agent.state": "listening"})

    vad_task = asyncio.create_task(process_vad())

    await session.start(
        agent=agent,
        room=ctx.room,
        room_input_options=room_io.RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
            audio_sample_rate=48000,
            audio_num_channels=1,
        )
    )
    await ctx.connect()

    await vad_task


if __name__ == "__main__":
    cli.run_app(server)
```
