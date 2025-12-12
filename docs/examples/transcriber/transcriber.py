"""
---
title: Transcriber
category: pipeline-stt
tags: [pipeline-stt, deepgram]
difficulty: beginner
description: Shows how to transcribe user speech to text without TTS or an LLM.
demonstrates:
  - Saving transcripts to a file.
  - An Agent that does not have TTS or an LLM. This is STT only.
---
"""

import datetime
from dotenv import load_dotenv
from livekit.agents import JobContext, AgentServer, cli, Agent, AgentSession, inference

load_dotenv()

server = AgentServer()

@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
    )

    @session.on("user_input_transcribed")
    def on_transcript(transcript):
        if transcript.is_final:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("user_speech_log.txt", "a") as f:
                f.write(f"[{timestamp}] {transcript.transcript}\n")

    await session.start(
        agent=Agent(instructions="You are a helpful assistant that transcribes user speech to text."),
        room=ctx.room
    )
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
