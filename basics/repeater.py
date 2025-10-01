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
from livekit.plugins import silero

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
            stt="assemblyai/universal-streaming",
            llm="openai/gpt-4.1-mini",
            tts="cartesia/sonic-2:6f84f4b8-58a2-430c-8c79-688dad597532",
            allow_interruptions=False,
            vad=silero.VAD.load()
        ),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))