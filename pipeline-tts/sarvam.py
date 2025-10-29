"""
---
title: Sarvam TTS and STT
category: pipeline-tts, pipeline-stt
tags: [pipeline-tts, pipeline-stt, sarvam]
difficulty: beginner
description: Shows how to use the Sarvam TTS and STT models.
demonstrates:
  - Using the Sarvam TTS and STT models.
---
"""
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import openai, sarvam, silero

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

class SarvamAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice. You're helping me test ... yourself ... since you're the AI agent. 
                Don't use any unpronouncable characters.
            """,
            stt=sarvam.STT(
                language="hi-IN",
                model="saarika:v2.5"
            ),
            llm=openai.LLM(model="gpt-4o-mini"),
            tts=sarvam.TTS(
                target_language_code="hi-IN",
                speaker="anushka"
            ),
            vad=silero.VAD.load()
        )
    
    async def on_enter(self):
        await self.session.say(f"Hi there! Is there anything I can help you with?")

async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=SarvamAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))