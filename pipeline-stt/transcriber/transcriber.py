"""
---
title: Transcriber
category: pipeline-stt
tags: [pipeline-stt, openai, deepgram]
difficulty: beginner
description: Shows how to transcribe user speech to text without TTS or an LLM.
demonstrates:
  - Saving transcripts to a file.
  - An Agent that does not have TTS or an LLM. This is STT only.
---
"""
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import deepgram
import datetime

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

async def entrypoint(ctx: JobContext):
    session = AgentSession()
    
    @session.on("user_input_transcribed")
    def on_transcript(transcript):
        if transcript.is_final:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("user_speech_log.txt", "a") as f:
                f.write(f"[{timestamp}] {transcript.transcript}\n") 
    
    await session.start(
        agent=Agent(
            instructions="You are a helpful assistant that transcribes user speech to text.",
            stt=deepgram.STT()
        ),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))