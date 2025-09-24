"""
---
title: Large Context Window LLM
category: pipeline-llm
tags: [gemini_2_flash, large_context, book_analysis, war_and_peace]
difficulty: intermediate
description: Agent using Gemini 2.0 Flash to analyze War and Peace with large context window
demonstrates:
  - Loading large text files into LLM context
  - Google Gemini 2.0 Flash model for large contexts
  - Book analysis and discussion capabilities
  - Direct text quotation from context
  - Custom TTS instructions for literary tone
---
"""

import logging
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import openai, google, deepgram, silero

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

logger = logging.getLogger("google_llm")
logger.setLevel(logging.INFO)

class WarAndPeaceAgent(Agent):
    def __init__(self) -> None:
        # Load War and Peace text content
        book_path = Path(__file__).parent / "lib" / "war_and_peace.txt"
        with open(book_path, "r", encoding="utf-8") as f:
            war_and_peace_text = f.read()

        super().__init__(
            instructions=f"""
                You are a War and Peace book club assistant. You help users discuss and understand Leo Tolstoy's novel "War and Peace."

                You can answer questions about the plot, characters, themes, historical context, and literary analysis of the book.

                Here is the complete text of the book that you can reference:

                {war_and_peace_text}

                Be concise but informative in your responses. If asked about specific passages, quote directly from the text.
            """,
            stt=deepgram.STT(),
            llm=google.LLM(model="gemini-2.0-flash"),
            tts=openai.TTS(instructions="You are a literary discussion assistant with a pleasant voice. Speak in a natural, conversational tone that conveys enthusiasm for literature."),
            vad=silero.VAD.load()
        )
    
    async def on_enter(self):
        self.session.generate_reply("Welcome to the War and Peace book club! I'm here to discuss Leo Tolstoy's epic novel with you. What would you like to talk about?")

async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=WarAndPeaceAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))