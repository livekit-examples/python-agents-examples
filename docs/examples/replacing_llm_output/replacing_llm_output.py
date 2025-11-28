"""
---
title: LLM Output Replacement
category: pipeline-llm
tags: [deepseek, groq, deepgram, openai]
difficulty: intermediate
description: Replaces Deepseek thinking tags with custom messages for TTS
demonstrates:
  - Groq integration with Deepseek model
  - Real-time stream processing
  - Text replacement in LLM output
  - Custom llm_node for output manipulation
  - Handling model-specific output formats
---
"""

import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession
from livekit.plugins import openai, deepgram, silero

load_dotenv()

logger = logging.getLogger("replacing-llm-output")
logger.setLevel(logging.INFO)

class SimpleAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="You are a helpful agent."
        )
        self._llm = openai.LLM.with_groq(model="deepseek-r1-distill-llama-70b")

    async def on_enter(self):
        self.session.generate_reply()

    async def llm_node(self, chat_ctx, tools, model_settings=None):
        async def process_stream():
            async with self._llm.chat(chat_ctx=chat_ctx, tools=tools, tool_choice=None) as stream:
                async for chunk in stream:
                    if chunk is None:
                        continue

                    content = getattr(chunk.delta, 'content', None) if hasattr(chunk, 'delta') else str(chunk)
                    if content is None:
                        yield chunk
                        continue

                    processed_content = content.replace("<think>", "").replace("</think>", "Okay, I'm ready to respond.")
                    print(f"Original: {content}, Processed: {processed_content}")

                    if processed_content != content:
                        if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'content'):
                            chunk.delta.content = processed_content
                        else:
                            chunk = processed_content

                    yield chunk

        return process_stream()

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=deepgram.STT(),
        tts=openai.TTS(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(agent=SimpleAgent(), room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
