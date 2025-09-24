"""
---
title: LLM Output Replacement
category: pipeline-llm
tags: [deepseek, groq, stream_manipulation, think_tags, output_processing]
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

# In this example, we replace the <think> tags returned by Deepseek with a custom message,
# so that the TTS engine doesn't say the <think> tags as part of the response.

import logging
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import openai, deepgram, silero

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

logger = logging.getLogger("replacing-llm-output")
logger.setLevel(logging.INFO)

class SimpleAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent.
            """,
            stt=deepgram.STT(),
            llm=openai.LLM.with_groq(model="deepseek-r1-distill-llama-70b"),
            tts=openai.TTS(),
            vad=silero.VAD.load()
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
                    
                    processed_content = content.replace("<think>", "").replace("</think>", "Okay, I'm ready to respond.")
                    print(f"Original: {content}, Processed: {processed_content}")
                    
                    if processed_content != content:
                        if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'content'):
                            chunk.delta.content = processed_content
                        else:
                            chunk = processed_content
                    
                    yield chunk

        return process_stream()

async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=SimpleAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))