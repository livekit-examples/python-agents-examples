"""
---
title: PlayAI TTS
category: pipeline-tts
tags: [pipeline-tts, openai, deepgram]
difficulty: intermediate
description: Shows how to use the PlayAI TTS model.
demonstrates:
  - Using the PlayAI TTS model.
---
"""
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import deepgram, openai, playai, silero

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

class PlayAIAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice. You're helping me test ... yourself ... since you're the AI agent. 
                Don't use any unpronouncable characters.
            """,
            stt=deepgram.STT(),
            llm=openai.LLM(model="gpt-4o"),
            tts=playai.TTS(
                model="PlayDialog",
                sample_rate=44100,
                voice="s3://voice-cloning-zero-shot/9f1ee23a-9108-4538-90be-8e62efc195b6/charlessaad/manifest.json"
            ),
            vad=silero.VAD.load()
        )
    
    async def on_enter(self):
        await self.session.say(f"Hi there! Is there anything I can help you with?")

async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=PlayAIAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))