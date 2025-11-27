"""
---
title: Keyword Detection
category: pipeline-stt
tags: [pipeline-stt, assemblyai, openai, cartesia]
difficulty: intermediate
description: Shows how to detect keywords in user speech.
demonstrates:
  - If the user says a keyword, the agent will log the keyword to the console.
  - Using the `stt_node` method to override the default STT node and add custom logic to detect keywords.
---
"""
import logging
from typing import AsyncIterable, Optional
from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import JobContext, WorkerOptions, cli, Agent, AgentSession
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("keyword-detection")
logger.setLevel(logging.INFO)

class KeywordDetectionAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent that detects keywords in user speech.
            """,
            stt=inference.STT(
                model="assemblyai/universal-streaming",
                language="en"
            ),
            llm=inference.LLM(
                model="openai/gpt-5-mini",
                provider="openai",
            ),
            tts=inference.TTS(
                model="cartesia/sonic-3",
                voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
            ),
            vad=silero.VAD.load()
        )

    async def on_enter(self):
        self.session.generate_reply()

    async def stt_node(self, text: AsyncIterable[str], model_settings: Optional[dict] = None) -> Optional[AsyncIterable[rtc.AudioFrame]]:
        keywords = ["Shane", "hello", "thanks", "bye"]
        parent_stream = super().stt_node(text, model_settings)

        if parent_stream is None:
            return None

        async def process_stream():
            async for event in parent_stream:
                if hasattr(event, 'type') and str(event.type) == "SpeechEventType.FINAL_TRANSCRIPT" and event.alternatives:
                    transcript = event.alternatives[0].text

                    for keyword in keywords:
                        if keyword.lower() in transcript.lower():
                            logger.info(f"Keyword detected: '{keyword}'")

                yield event

        return process_stream()

async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=KeywordDetectionAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
