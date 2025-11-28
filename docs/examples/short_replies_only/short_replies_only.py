"""
---
title: Short Replies Only
category: pipeline-tts
tags: [pipeline-tts, openai, deepgram, rime]
difficulty: beginner
description: Shows how to override the default TTS node to only respond with short replies based on the number of chunks.
demonstrates:
  - Using the `tts_node` method to override the default TTS node and add custom logic to only respond with short replies.
  - Using the `session.interrupt` method to interrupt the agent if it's taking too long to respond, and then informing the user with `session.say`
---
"""
from typing import AsyncIterable
import logging
from dotenv import load_dotenv
from livekit.agents import AgentServer, AgentSession, JobContext, JobProcess, cli, Agent, inference, ModelSettings
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("tts_node")
logger.setLevel(logging.INFO)

class ShortRepliesOnlyAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice.
            """,
        )

    async def tts_node(self, text: AsyncIterable[str], model_settings: ModelSettings):
        MAX_CHUNKS = 20
        chunk_count = 0

        async def process_text():
            nonlocal chunk_count
            interrupted = False
            async for chunk in text:
                chunk_count += 1
                if chunk_count > MAX_CHUNKS and not interrupted:
                    logger.info(f"tts_node: Exceeded {MAX_CHUNKS} chunks. Interrupting.")
                    self.session.interrupt()
                    self.session.say("I'm sorry, that will take too long to say.")
                    interrupted = True
                    break

                if not interrupted:
                    yield chunk

        return Agent.default.tts_node(self, process_text(), model_settings)

    async def on_enter(self):
        await self.session.say("Hi there! Is there anything I can help you with?")

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3", language="en"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(model="rime/arcana"),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )
    agent = ShortRepliesOnlyAgent()

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
