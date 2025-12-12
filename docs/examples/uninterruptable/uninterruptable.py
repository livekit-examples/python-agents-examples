"""
---
title: Uninterruptable Agent
category: basics
tags: [interruptions, allow_interruptions, agent_configuration, deepgram, openai, cartesia]
difficulty: beginner
description: Agent configured to complete responses without user interruptions
demonstrates:
  - Setting allow_interruptions=False in agent configuration
  - Testing interruption handling behavior
  - Agent-initiated conversation with on_enter
---
"""

from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession, inference
from livekit.plugins import silero

load_dotenv()

class UninterruptableAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful assistant communicating through voice who is not interruptable.
            """,
            allow_interruptions=False
        )

    async def on_enter(self):
        self.session.generate_reply(user_input="Say something somewhat long and boring so I can test if you're interruptable.")

server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm

@server.rtc_session()
async def entrypoint(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3-general"),
        llm=inference.LLM(model="openai/gpt-4.1-mini"),
        tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(agent=UninterruptableAgent(), room=ctx.room)
    await ctx.connect()

if __name__ == "__main__":
    cli.run_app(server)
