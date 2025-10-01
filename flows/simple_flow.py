"""
---
title: Simple Flow
category: flows
tags: [flows, openai, assemblyai]
difficulty: beginner
description: Shows how to create a simple one-way flow using a series of agents.
demonstrates:
  - Creating a simple one-way flow using a series of agents that hand off to the next agent in the flow.
---
"""
import logging
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.llm import function_tool
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import silero
from livekit import api

# Load environment and configure logger
load_dotenv()
logger = logging.getLogger("simple-flow")
logger.setLevel(logging.INFO)

class BaseAgent(Agent):
    def __init__(self, job_context: JobContext, instructions: str) -> None:
        self.job_context = job_context
        super().__init__(
            instructions=instructions,
            stt="assemblyai/universal-streaming",
            llm="openai/gpt-4.1-mini",
            tts="cartesia/sonic-2:6f84f4b8-58a2-430c-8c79-688dad597532",
            vad=silero.VAD.load()
        )

class GreetingAgent(BaseAgent):
    def __init__(self, job_context: JobContext) -> None:
        super().__init__(
            job_context=job_context,
            instructions="""
                You are a helpful assistant. Start by greeting the user and asking for their name.
            """
        )

    async def on_enter(self) -> None:
        await self.session.say("Hello! I'm here to help you. What's your name?")

    @function_tool
    async def collect_name(self, name: str) -> Agent:
        """
        Receive the user's name, acknowledge it, and transition to asking their favorite color.
        """
        await self.session.say(f"Hello, {name}! Nice to meet you.")
        return AskColorAgent(name=name, job_context=self.job_context)

class AskColorAgent(BaseAgent):
    def __init__(self, name: str, job_context: JobContext) -> None:
        super().__init__(
            job_context=job_context,
            instructions=f"You are talking to {name}. Ask the user what their favorite color is."
        )
        self.name = name

    async def on_enter(self) -> None:
        await self.session.say(f"{self.name}, what is your favorite color?")

    @function_tool
    async def collect_color(self, color: str) -> Agent:
        """
        Receive the user's favorite color, acknowledge it, and transition to summary.
        """
        await self.session.say(f"{color} is a wonderful choice!")
        return SummaryAgent(name=self.name, color=color, job_context=self.job_context)

class SummaryAgent(BaseAgent):
    def __init__(self, name: str, color: str, job_context: JobContext) -> None:
        super().__init__(
            job_context=job_context,
            instructions="Summarize the collected information and end the conversation."
        )
        self.name = name
        self.color = color

    async def on_enter(self) -> None:
        await self.session.say(
            f"Thank you, {self.name}. I have learned that your favorite color is {self.color}. Goodbye!"
        )
        logger.info("Closing session")
        await self.session.aclose()

        logger.info("Deleting room")
        request = api.DeleteRoomRequest(room=self.job_context.room.name)
        await self.job_context.api.room.delete_room(request)

async def entrypoint(ctx: JobContext) -> None:
    session = AgentSession()
    await session.start(
        agent=GreetingAgent(
            job_context=ctx
        ),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))