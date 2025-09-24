"""
---
title: AWS Realtime Voice Agent
category: realtime-agents
tags: [aws_realtime, aws_bedrock, nova_model]
difficulty: beginner
description: Voice agent using AWS Bedrock Nova Realtime model
demonstrates:
  - AWS Realtime model integration
  - AWS Bedrock Nova model usage
  - Context connection before session
  - Minimal agent with AWS
---
"""

from dotenv import load_dotenv
from pathlib import Path
from livekit import agents
from livekit.agents.voice import AgentSession, Agent
from livekit.plugins import (
    openai,
    aws,
    silero
)

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="You are a helpful voice AI assistant. Please speak in english!")

async def entrypoint(ctx: agents.JobContext):
    await ctx.connect()

    session = AgentSession(
        llm=aws.realtime.RealtimeModel(),
        vad=silero.VAD.load()
    )

    await session.start(
        room=ctx.room,
        agent=Assistant()
    )

    await session.generate_reply()

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))