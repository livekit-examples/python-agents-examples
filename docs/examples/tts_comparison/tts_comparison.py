"""
---
title: TTS Comparison
category: pipeline-tts
tags: [pipeline-tts, deepgram, openai, rime, elevenlabs, cartesia, playai]
difficulty: intermediate
description: Switches between different TTS providers using function tools.
demonstrates:
  - Using function tools to switch between different TTS providers.
  - Each function tool returns a new agent with the same instructions, but with a different TTS provider.
---
"""

import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession, function_tool
from livekit.plugins import deepgram, openai, rime, elevenlabs, cartesia, playai, silero

logger = logging.getLogger("tts-comparison")
logger.setLevel(logging.INFO)

load_dotenv()

class RimeAgent(Agent):
    def __init__(self, vad) -> None:
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
            vad=vad
        )
        self._vad = vad

    async def on_enter(self) -> None:
        await self.session.say("Hello! I'm now using the Rime TTS voice. How does it sound?")

    @function_tool
    async def switch_to_elevenlabs(self):
        """Switch to ElevenLabs TTS voice"""
        return ElevenLabsAgent(self._vad)

    @function_tool
    async def switch_to_cartesia(self):
        """Switch to Cartesia TTS voice"""
        return CartesiaAgent(self._vad)

    @function_tool
    async def switch_to_playai(self):
        """Switch to PlayAI TTS voice"""
        return PlayAIAgent(self._vad)


class ElevenLabsAgent(Agent):
    def __init__(self, vad) -> None:
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
            vad=vad
        )
        self._vad = vad

    async def on_enter(self) -> None:
        await self.session.say("Hello! I'm now using the ElevenLabs TTS voice. What do you think of how I sound?")

    @function_tool
    async def switch_to_rime(self):
        """Switch to Rime TTS voice"""
        return RimeAgent(self._vad)

    @function_tool
    async def switch_to_cartesia(self):
        """Switch to Cartesia TTS voice"""
        return CartesiaAgent(self._vad)

    @function_tool
    async def switch_to_playai(self):
        """Switch to PlayAI TTS voice"""
        return PlayAIAgent(self._vad)


class CartesiaAgent(Agent):
    def __init__(self, vad) -> None:
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
            vad=vad
        )
        self._vad = vad

    async def on_enter(self) -> None:
        await self.session.say("Hello! I'm now using the Cartesia TTS voice. How do I sound to you?")

    @function_tool
    async def switch_to_rime(self):
        """Switch to Rime TTS voice"""
        return RimeAgent(self._vad)

    @function_tool
    async def switch_to_elevenlabs(self):
        """Switch to ElevenLabs TTS voice"""
        return ElevenLabsAgent(self._vad)

    @function_tool
    async def switch_to_playai(self):
        """Switch to PlayAI TTS voice"""
        return PlayAIAgent(self._vad)


class PlayAIAgent(Agent):
    def __init__(self, vad) -> None:
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
            vad=vad
        )
        self._vad = vad

    async def on_enter(self) -> None:
        await self.session.say("Hello! I'm now using the PlayAI TTS voice. What are your thoughts on how I sound?")

    @function_tool
    async def switch_to_rime(self):
        """Switch to Rime TTS voice"""
        return RimeAgent(self._vad)

    @function_tool
    async def switch_to_elevenlabs(self):
        """Switch to ElevenLabs TTS voice"""
        return ElevenLabsAgent(self._vad)

    @function_tool
    async def switch_to_cartesia(self):
        """Switch to Cartesia TTS voice"""
        return CartesiaAgent(self._vad)


server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession()

    await session.start(
        agent=RimeAgent(vad=ctx.proc.userdata["vad"]),
        room=ctx.room
    )
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
