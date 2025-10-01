"""
---
title: IVR Phone System Navigator
category: complex-agents
tags: [ivr, dtmf, telephony, sip, participant_attributes, cooldown]
difficulty: advanced
description: Agent that navigates phone IVR systems using DTMF codes
demonstrates:
  - DTMF code transmission for phone navigation
  - SIP participant detection and handling
  - Task extraction from participant attributes
  - Cooldown mechanism for DTMF presses
  - Dynamic instruction updates based on task
  - Function tool for sending DTMF codes
---
"""

from __future__ import annotations
import time
import asyncio
import logging
from dataclasses import dataclass
from typing import Annotated, Optional
from pathlib import Path
from dotenv import load_dotenv
from livekit import rtc
from livekit import agents
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.llm import function_tool
from livekit.agents.voice import Agent, AgentSession, RunContext
from livekit.plugins import openai, silero, cartesia, deepgram
from pydantic import Field

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

logger = logging.getLogger("my-worker")
logger.setLevel(logging.INFO)

@dataclass
class UserData:
    """Store user data for the navigator agent."""
    ctx: JobContext
    last_dtmf_press: float = 0
    task: Optional[str] = None

RunContext_T = RunContext[UserData]

class NavigatorAgent(Agent):
    """Agent that navigates through phone IVR systems."""

    def __init__(self) -> None:
        """Initialize the navigator agent."""
        super().__init__(instructions="")

    async def on_enter(self) -> None:
        """Called when the agent is first activated."""
        logger.info("NavigatorAgent activated")

        # Get the task from userdata
        task = self.session.userdata.task
        if task:
            # Update the agent with task-specific instructions
            instructions = (
                f"""
                You are a person who is calling a phone number to accomplish a task.
                Speak from the perspective of the caller.
                Your goal as the caller is to: {task}.
                Listen carefully and pick the most appropriate option from the IVR menu.
                """
            )
            await self.update_instructions(instructions)

    @function_tool()
    async def send_dtmf_code(
        self,
        code: Annotated[int, Field(description="The DTMF code to send to the phone number for the current step.")],
        context: RunContext_T
    ) -> None:
        """Called when you need to send a DTMF code to the phone number for the current step."""
        current_time = time.time()

        # Check if enough time has passed since last press (3 second cooldown)
        if current_time - context.userdata.last_dtmf_press < 3:
            logger.info("DTMF code rejected due to cooldown")
            return None

        logger.info(f"Sending DTMF code {code} to the phone number for the current step.")
        context.userdata.last_dtmf_press = current_time

        room = context.userdata.ctx.room

        await room.local_participant.publish_dtmf(
            code=code,
            digit=str(code)
        )
        await room.local_participant.publish_data(
            f"{code}",
            topic="dtmf_code"
        )
        return None


async def entrypoint(ctx: JobContext):
    """Main entry point for the navigator agent."""
    logger.info("starting entrypoint")
    logger.info(f"connecting to room {ctx.room.name}")

    # Connect to the room
    await ctx.connect(auto_subscribe=agents.AutoSubscribe.AUDIO_ONLY)

    # Setup participant connection handler
    @ctx.room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant):
        logger.info(f"new participant joined {participant.identity}")
        if not "sip_" in participant.identity:
            return

        # Get the task from attributes
        task = participant._info.attributes.get("task")
        logger.info(f"task: {task}")

        # Initialize user data
        userdata = UserData(ctx=ctx, task=task)

        # Create and start the agent session
        session = AgentSession(
            userdata=userdata,
            stt="assemblyai/universal-streaming",
            llm="openai/gpt-4.1-mini",
            tts="cartesia/sonic-2:6f84f4b8-58a2-430c-8c79-688dad597532",
            vad=silero.VAD.load(),
            min_endpointing_delay=0.75
        )

        # Start the navigator agent
        asyncio.create_task(
            session.start(
                room=ctx.room,
                agent=NavigatorAgent()
            )
        )

    # Wait for the first participant to connect
    await ctx.wait_for_participant()
    logger.info("Waiting for SIP participants to connect")


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
        ),
    )
