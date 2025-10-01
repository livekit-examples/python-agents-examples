"""
---
title: Multi-Stage Flow
category: flows
tags: [flows, openai, assemblyai]
difficulty: intermediate
description: Shows how to create a multi-stage flow using a series of agents.
demonstrates:
  - Creating a multi-stage flow using a series of agents.
---
"""
import logging
from dotenv import load_dotenv
from dataclasses import dataclass, field
from typing import Dict, List, Annotated
from enum import Enum
from pydantic import Field

from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.llm import function_tool
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import silero
from livekit import api

# Load environment and configure logger
load_dotenv()
logger = logging.getLogger("multi-stage-flow")
logger.setLevel(logging.INFO)

# Define enums for the choices at each stage
class Stage1Choice(str, Enum):
    OPTION_A = "A"
    OPTION_B = "B"

class Stage2Choice(str, Enum):
    OPTION_X = "X"
    OPTION_Y = "Y"

class Stage3Choice(str, Enum):
    OPTION_M = "M"
    OPTION_N = "N"

@dataclass
class SurveyData:
    """Stores all survey responses and state."""
    responses: Dict[str, str] = field(default_factory=dict)
    current_stage: int = 1
    current_branch: str = ""
    path_taken: List[str] = field(default_factory=list)

    def record(self, question: str, answer: str):
        self.responses[question] = answer
        self.path_taken.append(f"Stage {self.current_stage} ('{self.current_branch}') - {question}: {answer}")

class BaseAgent(Agent):
    """Base agent class handling job context and common setup."""
    def __init__(self, job_context: JobContext, instructions: str) -> None:
        self.job_context = job_context
        super().__init__(
            instructions=instructions,
            stt="assemblyai/universal-streaming",
            llm="openai/gpt-4.1-mini",
            tts="cartesia/sonic-2:6f84f4b8-58a2-430c-8c79-688dad597532",
            vad=silero.VAD.load()
        )

# Stage 1: Preference A or B
class Stage1Agent(BaseAgent):
    def __init__(self, job_context: JobContext) -> None:
        super().__init__(
            job_context=job_context,
            instructions="Stage 1: Do you prefer Option A or Option B?"
        )

    async def on_enter(self) -> None:
        await self.session.say("Stage 1: Do you prefer Option A or Option B?")

    @function_tool
    async def collect_stage1(
        self,
        choice: Annotated[
            Stage1Choice,
            Field(description="Do you prefer Option A or Option B?")
        ]
    ) -> Agent:
        sd: SurveyData = self.session.userdata
        sd.record("Prefer A or B", choice.value)
        sd.current_branch = choice.value
        if choice == Stage1Choice.OPTION_A:
            return Stage1ABranchAgent(job_context=self.job_context)
        return Stage1BBranchAgent(job_context=self.job_context)

class Stage1ABranchAgent(BaseAgent):
    def __init__(self, job_context: JobContext) -> None:
        super().__init__(
            job_context=job_context,
            instructions="Follow-up: Why do you prefer Option A?"
        )

    async def on_enter(self) -> None:
        await self.session.say("Why do you prefer Option A?")

    @function_tool
    async def collect_A(self, answer: str) -> Agent:
        sd: SurveyData = self.session.userdata
        sd.record("Why prefer A", answer)
        sd.current_stage = 2
        return Stage2Agent(job_context=self.job_context)

class Stage1BBranchAgent(BaseAgent):
    def __init__(self, job_context: JobContext) -> None:
        super().__init__(
            job_context=job_context,
            instructions="Follow-up: Why do you prefer Option B?"
        )

    async def on_enter(self) -> None:
        await self.session.say("Why do you prefer Option B?")

    @function_tool
    async def collect_B(self, answer: str) -> Agent:
        sd: SurveyData = self.session.userdata
        sd.record("Why prefer B", answer)
        sd.current_stage = 2
        return Stage2Agent(job_context=self.job_context)

# Stage 2: Preference X or Y
class Stage2Agent(BaseAgent):
    def __init__(self, job_context: JobContext) -> None:
        super().__init__(
            job_context=job_context,
            instructions="Stage 2: Do you prefer Option X or Option Y?"
        )

    async def on_enter(self) -> None:
        await self.session.say("Stage 2: Do you prefer Option X or Option Y?")

    @function_tool
    async def collect_stage2(
        self,
        choice: Annotated[
            Stage2Choice,
            Field(description="Do you prefer Option X or Option Y?")
        ]
    ) -> Agent:
        sd: SurveyData = self.session.userdata
        sd.record("Prefer X or Y", choice.value)
        sd.current_branch = choice.value
        if choice == Stage2Choice.OPTION_X:
            return Stage2XBranchAgent(job_context=self.job_context)
        return Stage2YBranchAgent(job_context=self.job_context)

class Stage2XBranchAgent(BaseAgent):
    def __init__(self, job_context: JobContext) -> None:
        super().__init__(
            job_context=job_context,
            instructions="Follow-up: What appeals to you about Option X?"
        )

    async def on_enter(self) -> None:
        await self.session.say("What appeals to you about Option X?")

    @function_tool
    async def collect_X(self, answer: str) -> Agent:
        sd: SurveyData = self.session.userdata
        sd.record("Appeal of X", answer)
        sd.current_stage = 3
        return Stage3Agent(job_context=self.job_context)

class Stage2YBranchAgent(BaseAgent):
    def __init__(self, job_context: JobContext) -> None:
        super().__init__(
            job_context=job_context,
            instructions="Follow-up: What appeals to you about Option Y?"
        )

    async def on_enter(self) -> None:
        await self.session.say("What appeals to you about Option Y?")

    @function_tool
    async def collect_Y(self, answer: str) -> Agent:
        sd: SurveyData = self.session.userdata
        sd.record("Appeal of Y", answer)
        sd.current_stage = 3
        return Stage3Agent(job_context=self.job_context)

# Stage 3: Preference M or N
class Stage3Agent(BaseAgent):
    def __init__(self, job_context: JobContext) -> None:
        super().__init__(
            job_context=job_context,
            instructions="Stage 3: Do you prefer Option M or Option N?"
        )

    async def on_enter(self) -> None:
        await self.session.say("Stage 3: Do you prefer Option M or Option N?")

    @function_tool
    async def collect_stage3(
        self,
        choice: Annotated[
            Stage3Choice,
            Field(description="Do you prefer Option M or Option N?")
        ]
    ) -> Agent:
        sd: SurveyData = self.session.userdata
        sd.record("Prefer M or N", choice.value)
        branch = choice.value
        if choice == Stage3Choice.OPTION_M:
            return Stage3MBranchAgent(job_context=self.job_context)
        return Stage3NBranchAgent(job_context=self.job_context)

class Stage3MBranchAgent(BaseAgent):
    def __init__(self, job_context: JobContext) -> None:
        super().__init__(
            job_context=job_context,
            instructions="Follow-up: Why do you prefer Option M?"
        )

    async def on_enter(self) -> None:
        await self.session.say("Why do you prefer Option M?")

    @function_tool
    async def collect_M(self, answer: str) -> Agent:
        sd: SurveyData = self.session.userdata
        sd.record("Why M", answer)
        return SummaryAgent(job_context=self.job_context)

class Stage3NBranchAgent(BaseAgent):
    def __init__(self, job_context: JobContext) -> None:
        super().__init__(
            job_context=job_context,
            instructions="Follow-up: Why do you prefer Option N?"
        )

    async def on_enter(self) -> None:
        await self.session.say("Why do you prefer Option N?")

    @function_tool
    async def collect_N(self, answer: str) -> Agent:
        sd: SurveyData = self.session.userdata
        sd.record("Why N", answer)
        return SummaryAgent(job_context=self.job_context)

class SummaryAgent(BaseAgent):
    def __init__(self, job_context: JobContext) -> None:
        super().__init__(
            job_context=job_context,
            instructions="Summarize all responses and end the survey."
        )

    async def on_enter(self) -> None:
        sd: SurveyData = self.session.userdata
        summary = "Thank you for completing the survey! Here are your responses:\n"
        for q, a in sd.responses.items():
            summary += f"- {q}: {a}\n"
        await self.session.say(summary)
        logger.info("Survey complete. Closing session.")
        await self.session.aclose()
        try:
            await self.job_context.api.room.delete_room(
                api.DeleteRoomRequest(room=self.job_context.room.name)
            )
        except Exception as e:
            logger.error(f"Error deleting room: {e}")

async def entrypoint(ctx: JobContext) -> None:
    session = AgentSession()
    session.userdata = SurveyData()
    await session.start(
        agent=Stage1Agent(job_context=ctx),
        room=ctx.room
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))