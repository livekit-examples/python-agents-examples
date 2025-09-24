"""
---
title: Repeater
category: basics
tags: [repeater, openai, deepgram]
difficulty: beginner
description: Shows how to create an agent that can repeat what the user says.
demonstrates:
  - Using the `on_user_input_transcribed` event to listen to the user's input
  - Using the `say` method to respond to the user with the same input
---
"""
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import deepgram, openai

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

async def entrypoint(ctx: JobContext):
    session = AgentSession()
    
    @session.on("user_input_transcribed")
    def on_transcript(transcript):
        if transcript.is_final:
            session.say(transcript.transcript)           
    
    await session.start(
        agent=Agent(
            instructions="You are a helpful assistant that repeats what the user says.",
            stt=deepgram.STT(),
            tts=openai.TTS(),
            allow_interruptions=False
        ),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))