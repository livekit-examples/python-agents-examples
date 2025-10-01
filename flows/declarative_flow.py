"""
---
title: Declarative Flow
category: flows
tags: [flows, openai, assemblyai]
difficulty: intermediate
description: Shows how to create a declarative flow using a dictionary of mutliple agents and their transitions.
demonstrates:
  - Creating a defined flow of agents using a dictionary of mutliple agents and their transitions.
  - Using a function to determine the next agent in the flow.
---
"""
import logging
from dotenv import load_dotenv
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Type

from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.llm import function_tool
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import silero
from livekit import api

# Load environment and configure logger
load_dotenv()
logger = logging.getLogger("declarative-flow")
logger.setLevel(logging.INFO)

@dataclass
class SurveyData:
    """Stores all survey responses and state."""
    responses: Dict[str, str] = field(default_factory=dict)
    current_stage: str = "collect_name"
    path_taken: List[str] = field(default_factory=list)

    def record(self, question: str, answer: str):
        self.responses[question] = answer
        self.path_taken.append(f"Stage '{self.current_stage}' - {question}: {answer}")

class BaseAgent(Agent):
    """Base agent with common setup and transition logic."""
    def __init__(self, job_context: JobContext, instructions: str) -> None:
        self.job_context = job_context
        super().__init__(
            instructions=instructions,
            stt="assemblyai/universal-streaming",
            llm="openai/gpt-4.1-mini",
            tts="cartesia/sonic-2:6f84f4b8-58a2-430c-8c79-688dad597532",
            vad=silero.VAD.load()
        )

    async def transition(self) -> Optional[Agent]:
        """Move to the next agent based on the flow definition."""
        current = self.session.state.get("current_node")
        next_fn = flow.get(current, {}).get("next")
        if not next_fn:
            return None
        next_node = next_fn(self.session.state)
        if next_node is None:
            return None
        self.session.state["current_node"] = next_node
        agent_cls: Type[Agent] = flow[next_node]["agent"]
        return agent_cls(self.job_context)

class DataCollectorAgent(BaseAgent):
    """Generic agent for collecting a single piece of data and transitioning."""
    key: str
    label: str
    question: str
    instruction: str

    def __init__(self, job_context: JobContext) -> None:
        super().__init__(job_context=job_context, instructions=self.instruction)

    async def on_enter(self) -> None:
        await self.session.say(self.question)

    @function_tool
    async def collect(self, value: str) -> Optional[Agent]:
        sd: SurveyData = self.session.userdata
        sd.record(self.label, value)
        self.session.state[self.key] = value
        return await self.transition()

class CollectNameAgent(DataCollectorAgent):
    key = "name"
    label = "Name"
    question = "What is your name?"
    instruction = "Please tell me your name."

class CollectEmailAgent(DataCollectorAgent):
    key = "email"
    label = "Email"
    question = "What is your email address?"
    instruction = "Please tell me your email address."

class SummaryAgent(BaseAgent):
    def __init__(self, job_context: JobContext) -> None:
        super().__init__(job_context=job_context, instructions="Summary of your information.")

    async def on_enter(self) -> None:
        sd: SurveyData = self.session.userdata
        name = sd.responses.get("Name", "[not provided]")
        email = sd.responses.get("Email", "[not provided]")
        summary = f"Thank you! Here is what I collected:\n- Name: {name}\n- Email: {email}"
        await self.session.say(summary)
        logger.info("Survey complete. Closing session.")
        await self.session.aclose()
        try:
            await self.job_context.api.room.delete_room(
                api.DeleteRoomRequest(room=self.job_context.room.name)
            )
        except Exception as e:
            logger.error(f"Error deleting room: {e}")

flow = {
    "collect_name": {
        "agent": CollectNameAgent,
        "next": lambda state: "collect_email"
    },
    "collect_email": {
        "agent": CollectEmailAgent,
        "next": lambda state: "summary"
    },
    "summary": {
        "agent": SummaryAgent,
        "next": None
    }
}

async def entrypoint(ctx: JobContext) -> None:
    session = AgentSession()
    session.userdata = SurveyData()
    session.state = {"current_node": "collect_name"}
    await session.start(agent=CollectNameAgent(ctx), room=ctx.room)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
