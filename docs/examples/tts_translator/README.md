---
title: TTS Translator with Gladia STT
category: translation
tags: [translation, gladia, elevenlabs, multilingual, code-switching, event-handling]
difficulty: advanced
description: Advanced translation system using Gladia STT with code switching and event handling
demonstrates:
  - Gladia STT integration with multiple languages
  - Code switching between French and English
  - Translation event handling and processing
  - Custom STT configuration with translation capabilities
  - Event-driven transcription and speech synthesis
  - Advanced multilingual processing pipeline
---

This example wires up Gladia's STT with code switching and on-the-fly translation. The agent accepts French or English, translates to English, and speaks back with ElevenLabs TTS.

## Prerequisites

- Add a `.env` in this directory with your LiveKit credentials:
  ```
  LIVEKIT_URL=your_livekit_url
  LIVEKIT_API_KEY=your_api_key
  LIVEKIT_API_SECRET=your_api_secret
  GLADIA_API_KEY=your_gladia_key
  ELEVENLABS_API_KEY=your_elevenlabs_key
  ```
- Install dependencies:
  ```bash
  pip install "livekit-agents[silero]" python-dotenv livekit-plugins-gladia livekit-plugins-elevenlabs
  ```

## Load configuration and create the AgentServer

Load environment variables so the Gladia and ElevenLabs plugins can authenticate. Create an AgentServer to manage sessions.

```python
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession
from livekit.plugins import elevenlabs, silero, gladia

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

## Configure Gladia STT for code-switching and translation

Set up STT to accept both French and English, allow code switching mid-utterance, and translate everything to English before TTS.

```python
stt=gladia.STT(
    languages=["fr", "en"],
    code_switching=True,
    sample_rate=16000,
    bit_depth=16,
    channels=1,
    encoding="wav/pcm",
    translation_enabled=True,
    translation_target_languages=["en"],
    translation_model="base",
    translation_match_original_utterances=True
)
```

## Handle transcription events

Listen for `user_input_transcribed` to see raw and translated text. When a final transcript arrives, speak it back with ElevenLabs.

```python
@session.on("user_input_transcribed")
def on_transcript(event):
    print(f"Transcript event: {event}")
    if event.is_final:
        print(f"Final transcript: {event.transcript}")
        session.say(event.transcript)
```

## Create the RTC session entrypoint

Build a minimal agent without an LLM. Gladia handles translation and the transcript is read aloud via ElevenLabs multilingual TTS.

```python
@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession()

    @session.on("user_input_transcribed")
    def on_transcript(event):
        print(f"Transcript event: {event}")
        if event.is_final:
            print(f"Final transcript: {event.transcript}")
            session.say(event.transcript)

    await session.start(
        agent=Agent(
            instructions="You are a helpful assistant that speaks what the user says in English.",
            stt=gladia.STT(
                languages=["fr", "en"],
                code_switching=True,
                sample_rate=16000,
                bit_depth=16,
                channels=1,
                encoding="wav/pcm",
                translation_enabled=True,
                translation_target_languages=["en"],
                translation_model="base",
                translation_match_original_utterances=True
            ),
            tts=elevenlabs.TTS(model="eleven_multilingual_v2"),
            allow_interruptions=False,
            vad=ctx.proc.userdata["vad"]
        ),
        room=ctx.room
    )
    await ctx.connect()
```

## Run it

```console
python tts_translator.py console
```

## How it works

1. Gladia STT accepts French and English, allowing code-switching within an utterance.
2. Translation runs inside STT, producing English text even for French input.
3. The session listens for transcript events and speaks the final text with ElevenLabs.
4. Interruptions are disabled so the agent finishes playing the translated audio.

## Full example

```python
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession
from livekit.plugins import elevenlabs, silero, gladia

load_dotenv()

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession()

    @session.on("user_input_transcribed")
    def on_transcript(event):
        print(f"Transcript event: {event}")
        if event.is_final:
            print(f"Final transcript: {event.transcript}")
            session.say(event.transcript)

    await session.start(
        agent=Agent(
            instructions="You are a helpful assistant that speaks what the user says in English.",
            stt=gladia.STT(
                languages=["fr", "en"],
                code_switching=True,
                sample_rate=16000,
                bit_depth=16,
                channels=1,
                encoding="wav/pcm",
                translation_enabled=True,
                translation_target_languages=["en"],
                translation_model="base",
                translation_match_original_utterances=True
            ),
            tts=elevenlabs.TTS(model="eleven_multilingual_v2"),
            allow_interruptions=False,
            vad=ctx.proc.userdata["vad"]
        ),
        room=ctx.room
    )
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
```
