"""
---
title: Function Tool Voice Switching Agent
category: basics
tags: [tts, voice-switching, function-tools, inworld, deepgram, openai]
difficulty: beginner
description: Demonstrates how to create an agent that can dynamically switch between different voices during a conversation using function tools.
demonstrates:
  - Dynamic TTS voice switching
  - Function tool integration
  - Multiple TTS provider support (Inworld)
---
"""

import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession, inference, function_tool
from livekit.plugins import silero, inworld

load_dotenv()

logger = logging.getLogger("say-in-voice")
logger.setLevel(logging.INFO)

class SayPhraseInVoiceAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="You are an agent that can say phrases in different voices."
        )
        self._tts = inworld.TTS(voice="Ashley")

    async def say_phrase_in_voice(self, phrase, voice="Hades"):
        self._tts.update_options(voice=voice)
        await self.session.say(phrase)
        self._tts.update_options(voice="Ashley")

    @function_tool
    async def say_phrase_in_voice_tool(self, phrase: str, voice: str = "Ashley"):
        """Say a phrase in a specific voice"""
        await self.say_phrase_in_voice(phrase, voice)

    async def on_enter(self):
        self.session.generate_reply()

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    agent = SayPhraseInVoiceAgent()

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-5-mini"),
        tts=agent._tts,
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(agent=agent, room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
