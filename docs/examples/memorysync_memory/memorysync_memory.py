"""
---
title: MemorySync Long-Term Memory
category: integrations
tags: [memory, memorysync, deepgram, openai, cartesia]
difficulty: beginner
description: Gives the agent long-term memory with MemorySync, so it remembers callers across calls.
demonstrates:
  - Injecting recalled memories each turn under a hard latency budget
  - Capturing both user and assistant turns as durable memories
  - Adding a memory search tool the LLM can call on demand
---
"""

import logging

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    inference,
)
from livekit.plugins import silero
from livekit_memorysync import MemorySyncMemory, create_memory_search_tool

load_dotenv()

logger = logging.getLogger("memorysync-memory")
logger.setLevel(logging.INFO)


class MemoryAgent(Agent):
    def __init__(self, memory: MemorySyncMemory) -> None:
        super().__init__(
            instructions=(
                "You are a helpful voice assistant. Use anything you remember "
                "about the caller naturally, without reading it out verbatim."
            ),
            tools=[create_memory_search_tool(memory)],
        )
        self._memory = memory

    async def on_user_turn_completed(self, turn_ctx, new_message):
        # Injects recalled memories for THIS turn only, under a hard time
        # budget (default 1.2s). If the network is slow, the reply proceeds
        # without memories — never late.
        await self._memory.on_user_turn(turn_ctx, new_message)

    async def on_enter(self):
        self.session.generate_reply()


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    # In production, derive user_id from your auth (participant identity,
    # phone number, ...) so the same caller always maps to the same memories.
    memory = MemorySyncMemory(
        user_id="demo-caller",       # stable end-user id
        thread_id=ctx.room.name,     # scope this call's transcript to the room
    )

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )
    memory.attach(session)  # capture both user and assistant turns

    await session.start(agent=MemoryAgent(memory), room=ctx.room)
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)
