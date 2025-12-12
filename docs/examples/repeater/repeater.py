"""
---
title: Repeater
category: basics
tags: [repeater, deepgram, openai, cartesia]
difficulty: beginner
description: Shows how to create an agent that can repeat what the user says.
demonstrates:
  - Using the `on_user_input_transcribed` event to listen to the user's input
  - Using the `say` method to respond to the user with the same input
---
"""
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession, inference
from livekit.plugins import silero

load_dotenv()

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
        allow_interruptions=False,
    )

    @session.on("user_input_transcribed")
    def on_transcript(transcript):
        if transcript.is_final:
            session.say(transcript.transcript)

    await session.start(
        agent=Agent(
            instructions="You are a helpful assistant that repeats what the user says."
        ),
        room=ctx.room
    )
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
