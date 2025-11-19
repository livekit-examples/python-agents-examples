"""
---
title: Doheny Surf Desk Booking Agent
category: complex-agents
tags: [multi_agent, tasks, task_groups, observer_pattern, guardrails, typed_tasks, context_injection]
difficulty: advanced
description: Surf school booking system demonstrating typed tasks, task groups, and parallel observer with LLM-based guardrails
requires: livekit-agents>=1.3.0
demonstrates:
  - Sequential task execution with TaskGroup
  - Typed tasks with structured return values (ConsentTask, NotificationTask, PaymentDetailsTask)
  - Parallel observer agent using LLM-based evaluation for safety guardrails
  - Observer context injection pattern (hints injected into active agent's chat context)
  - Multi-agent workflow with 5 specialized agents and seamless handoffs
  - Context preservation across agent transitions
  - Minor consent collection and payment validation workflows
---
"""
import logging
from dotenv import load_dotenv

from livekit.agents import ConversationItemAddedEvent, JobContext, WorkerOptions, cli, RoomInputOptions
from livekit.agents.voice import AgentSession
from livekit.plugins import silero, noise_cancellation, openai
from livekit.plugins.turn_detector.multilingual import MultilingualModel


# Import agents
from agents.base_agent import SurfBookingData
from agents.frontdesk_agent import FrontDeskAgent
from agents.intake_agent import IntakeAgent
from agents.scheduler_agent import SchedulerAgent
from agents.gear_agent import GearAgent
from agents.billing_agent import BillingAgent
from agents.observer_agent import start_observer

# Load environment
load_dotenv(dotenv_path='.env')

logger = logging.getLogger("doheny-surf-desk")


async def entrypoint(ctx: JobContext):
    """Main entrypoint for Doheny Surf Desk booking agent.
    
    Sets up multi-agent session with:
    - FrontDeskAgent: Greets and provides consultation or routes to booking
    - IntakeAgent: Collects customer profile via sequential TaskGroup
    - SchedulerAgent: Books lesson time slot with availability checking
    - GearAgent: Recommends equipment based on measurements
    - BillingAgent: Processes payment and sends confirmation via tasks
    - ObserverAgent: Monitors for safety/compliance using LLM-based evaluation (parallel)
    """
    logger.info(f"Starting Doheny Surf Desk booking agent in room {ctx.room.name}")
    
    # Connect to the room
    await ctx.connect()
    
    # Initialize userdata for the session
    userdata = SurfBookingData()
    
    # Create all agent instances
    frontdesk_agent = FrontDeskAgent()
    intake_agent = IntakeAgent()
    scheduler_agent = SchedulerAgent()
    gear_agent = GearAgent()
    billing_agent = BillingAgent()
    
    # Register all agents in userdata for handoffs
    userdata.personas = {
        "frontdesk": frontdesk_agent,
        "intake": intake_agent,
        "scheduler": scheduler_agent,
        "gear": gear_agent,
        "billing": billing_agent,
    }
    
    # Create the agent session with LiveKit inference gateway
    session = AgentSession[SurfBookingData](
        userdata=userdata,
        vad=silero.VAD.load(),
        stt="deepgram/nova-2",
        llm="openai/gpt-4o",
        tts="cartesia/sonic-3:a167e0f3-df7e-4d52-a9c3-f949145efdab",
        turn_detection=MultilingualModel(),
    )

    # Start the observer agent in parallel
    # We will use another LLM for the observer agent (gpt-5 or any other thinking LLM, smarter but slower)
    # We can use anyother thinking LLM here. This is not realtime, so it's not a problem.
    # Otherwise we can share the same from main session.
    # This is why you need OPENAI_API_KEY in your .env file also.
    llm = openai.LLM(model="gpt-5")
    await start_observer(session, llm)
    
    # Start the session with FrontDeskAgent
    logger.info("Starting session with FrontDeskAgent")
    await session.start(
        agent=frontdesk_agent, # You can change the starting agent here to debug some specific part of the workflow
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))

