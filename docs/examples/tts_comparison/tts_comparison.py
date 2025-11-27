"""
---
title: TTS Comparison
category: pipeline-tts
tags: [pipeline-tts, openai, deepgram]
difficulty: intermediate
description: Switches between different TTS providers using function tools.
demonstrates:
  - Using function tools to switch between different TTS providers.
  - Each function tool returns a new agent with the same instructions, but with a different TTS provider.
---
"""
import logging
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, Agent, AgentSession, inference, function_tool
from livekit.plugins import deepgram, openai, rime, elevenlabs, cartesia, playai, silero

logger = logging.getLogger("tts-comparison")
logger.setLevel(logging.INFO)

load_dotenv(dotenv_path=Path(__file__).parents[3] / '.env')

class RimeAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice.
                You are currently using the Rime TTS provider.
                You can switch to a different TTS provider if asked.
                Don't use any unpronouncable characters.
            """,
            stt=deepgram.STT(),
            llm=openai.LLM(),
            tts=rime.TTS(),
            vad=silero.VAD.load()
        )

    async def on_enter(self) -> None:
        """Called when switching to this provider"""
        await self.session.say("Hello! I'm now using the Rime TTS voice. How does it sound?")

    @function_tool
    async def switch_to_elevenlabs(self):
        """Switch to ElevenLabs TTS voice"""
        return ElevenLabsAgent()

    @function_tool
    async def switch_to_cartesia(self):
        """Switch to Cartesia TTS voice"""
        return CartesiaAgent()

    @function_tool
    async def switch_to_playai(self):
        """Switch to PlayAI TTS voice"""
        return PlayAIAgent()


class ElevenLabsAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice.
                You are currently using the ElevenLabs TTS provider.
                You can switch to a different TTS provider if asked.
                Don't use any unpronouncable characters.
            """,
            stt=deepgram.STT(),
            llm=openai.LLM(),
            tts=elevenlabs.TTS(),
            vad=silero.VAD.load()
        )

    async def on_enter(self) -> None:
        """Called when switching to this provider"""
        await self.session.say("Hello! I'm now using the ElevenLabs TTS voice. What do you think of how I sound?")

    @function_tool
    async def switch_to_rime(self):
        """Switch to Rime TTS voice"""
        return RimeAgent()

    @function_tool
    async def switch_to_cartesia(self):
        """Switch to Cartesia TTS voice"""
        return CartesiaAgent()

    @function_tool
    async def switch_to_playai(self):
        """Switch to PlayAI TTS voice"""
        return PlayAIAgent()


class CartesiaAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice.
                You are currently using the Cartesia TTS provider.
                You can switch to a different TTS provider if asked.
                Don't use any unpronouncable characters.
            """,
            stt=deepgram.STT(),
            llm=openai.LLM(),
            tts=cartesia.TTS(),
            vad=silero.VAD.load()
        )

    async def on_enter(self) -> None:
        """Called when switching to this provider"""
        await self.session.say("Hello! I'm now using the Cartesia TTS voice. How do I sound to you?")

    @function_tool
    async def switch_to_rime(self):
        """Switch to Rime TTS voice"""
        return RimeAgent()

    @function_tool
    async def switch_to_elevenlabs(self):
        """Switch to ElevenLabs TTS voice"""
        return ElevenLabsAgent()

    @function_tool
    async def switch_to_playai(self):
        """Switch to PlayAI TTS voice"""
        return PlayAIAgent()


class PlayAIAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice.
                You are currently using the PlayAI TTS provider.
                You can switch to a different TTS provider if asked.
                Don't use any unpronouncable characters.
            """,
            stt=deepgram.STT(),
            llm=openai.LLM(),
            tts=playai.TTS(),
            vad=silero.VAD.load()
        )

    async def on_enter(self) -> None:
        """Called when switching to this provider"""
        await self.session.say("Hello! I'm now using the PlayAI TTS voice. What are your thoughts on how I sound?")

    @function_tool
    async def switch_to_rime(self):
        """Switch to Rime TTS voice"""
        return RimeAgent()

    @function_tool
    async def switch_to_elevenlabs(self):
        """Switch to ElevenLabs TTS voice"""
        return ElevenLabsAgent()

    @function_tool
    async def switch_to_cartesia(self):
        """Switch to Cartesia TTS voice"""
        return CartesiaAgent()


async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=RimeAgent(),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
