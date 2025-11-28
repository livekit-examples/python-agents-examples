"""
---
title: Simple Content Filter
category: pipeline-llm
tags: [pipeline-llm, openai, deepgram]
difficulty: beginner
description: Basic keyword-based content filter with inline replacement
demonstrates:
  - Simple keyword filtering approach
  - Inline content replacement
  - Custom llm_node override
  - Static offensive terms list
  - Stream processing with substitution
---
"""

import logging
from dotenv import load_dotenv
from livekit.agents import AgentServer, AgentSession, JobContext, JobProcess, cli, Agent, inference
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("simple-content-filter")
logger.setLevel(logging.INFO)

class SimpleAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent.
            """,
        )

    async def on_enter(self):
        self.session.generate_reply()

    async def llm_node(
        self, chat_ctx, tools, model_settings=None
    ):
        async def process_stream():
            async with self.llm.chat(chat_ctx=chat_ctx, tools=tools, tool_choice=None) as stream:
                async for chunk in stream:
                    if chunk is None:
                        continue

                    content = getattr(chunk.delta, 'content', None) if hasattr(chunk, 'delta') else str(chunk)
                    if content is None:
                        yield chunk
                        continue

                    offensive_terms = ['fail']
                    print(content)
                    yield "CONTENT FILTERED" if any(term in content.lower() for term in offensive_terms) else chunk

        return process_stream()

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3", language="en"),
        llm=inference.LLM(model="openai/gpt-5-mini"),
        tts=inference.TTS(
            model="cartesia/sonic-3", 
            voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"
        ),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )
    agent = SimpleAgent()

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
