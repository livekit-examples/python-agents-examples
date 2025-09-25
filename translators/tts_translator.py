"""
---
title: TTS Translator with Gladia STT
category: translation
tags: [translation, gladia-stt, multilingual, code-switching, event-handling]
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
"""

from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import elevenlabs, silero, gladia
import sys

sys.path.append(str(Path(__file__).parent.parent))

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

async def entrypoint(ctx: JobContext):
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
                languages=["fr", "en"],  # Support French and English input
                code_switching=True,
                sample_rate=16000,
                bit_depth=16,
                channels=1,
                encoding="wav/pcm",
                translation_enabled=True,
                translation_target_languages=["en"],  # Only translate to English
                translation_model="base",
                translation_match_original_utterances=True
            ),
            tts=elevenlabs.TTS(
                model="eleven_multilingual_v2"
            ),
            allow_interruptions=False,
            vad=silero.VAD.load()
        ),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))