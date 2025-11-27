"""
---
title: Conversation Event Monitoring Agent
category: basics
tags: [events, conversation-monitoring, logging, deepgram, openai]
difficulty: beginner
description: Shows how to monitor and log conversation events as they occur, useful for debugging and understanding agent-user interactions.
demonstrates:
  - Conversation event handling and logging
---
"""

import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, Agent, AgentSession, inference, ConversationItemAddedEvent
from livekit.plugins import silero

load_dotenv(dotenv_path=Path(__file__).parents[3] / '.env')

logger = logging.getLogger("label-messages")
logger.setLevel(logging.INFO)

class LabelMessagesAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent. When the user speaks, you listen and respond.
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

async def entrypoint(ctx: JobContext):
    await ctx.connect()

    session = AgentSession()

    @session.on("conversation_item_added")
    def conversation_item_added(item: ConversationItemAddedEvent):
        print(item)

    await session.start(
        agent=LabelMessagesAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
