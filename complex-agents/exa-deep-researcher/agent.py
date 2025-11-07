"""
---
title: EXA Deep Researcher
category: complex-agents
tags: [exa, research, voice_controlled, background_jobs, rpc_streaming]
difficulty: advanced
description: Voice-controlled deep research agent using EXA for web intelligence
demonstrates:
  - Voice-only control
  - Single background research job with state management
  - EXA API integration for search and content fetching
  - RPC streaming to UI for status, notes, and reports
  - Token-aware compression and concurrency control
  - Cited final reports saved to disk
---
"""
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Annotated
from dataclasses import dataclass, field
import os

from dotenv import load_dotenv
from pydantic import Field
from livekit.agents import (
    Agent, AgentSession, JobContext, WorkerOptions, cli, function_tool, RoomInputOptions
)
from livekit.agents.voice import RunContext
from livekit.plugins import silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.plugins import noise_cancellation

from agent.schemas import JobState
from agent.job_manager import JobManager

# Agent modules
from agent.handlers.status import StatusHandler
from agent.handlers.rpc import send_rpc_to_ui_safe
from agent.job_runner import run_research_job

# Research components
from agent.exa_client import EXAClient
from orchestrator import ResearchOrchestrator
from agent.prompts import supervisor_prompt

logger = logging.getLogger("exa-deep-researcher")
logger.setLevel(logging.INFO)

load_dotenv()


def get_agent_name() -> str:
    """Get agent name based on environment (dev or prod)"""
    if os.getenv("DEV"):
        return "exa-deep-researcher-dev"
    return "exa-deep-researcher"


@dataclass
class ExaUserData:
    """User data for EXA research agent"""
    ctx: JobContext
    session: Optional[AgentSession] = None
    job_manager: Optional[JobManager] = None
    exa_client: Optional[EXAClient] = None
    orchestrator: Optional[ResearchOrchestrator] = None
    status_handler: Optional[StatusHandler] = None
    status_queue: list = field(default_factory=list)
    status_task: Optional[asyncio.Task] = None


class ExaResearchAgent(Agent):
    """Voice-controlled deep research agent"""
    
    def __init__(self):
        super().__init__(
            instructions=supervisor_prompt(),
        )
    
    async def on_enter(self):
        """Called when agent enters the session"""
        self.session.say("Hey! I'm your research assistant. I can help you do deep research on any topic using EXA. Just tell me what you'd like to learn about!")
    
    @function_tool()
    async def start_research_job(
        self,
        context: RunContext[ExaUserData],
        query: Optional[str] = None,
        confirmed: Annotated[bool, Field(default=False)] = False,
    ) -> str:
        """
        Start a deep research job on a given topic. Only one job can run at a time.
        
        The system will first do a quick search to understand what you're looking for.
        If clarification is needed, it will ask you before starting the full research.
        
        Args:
            query: The research question or topic to investigate (optional if confirming)
            confirmed: Set to True if you're confirming after clarification (internal use)
            
        Returns:
            Confirmation message or clarification question
        """
        userdata = context.userdata
        job_manager = userdata.job_manager
        
        if not job_manager:
            job_manager = JobManager()
            userdata.job_manager = job_manager
        
        if job_manager.is_active():
            if job_manager.state == JobState.CLARIFYING and (confirmed or (query and query != job_manager.original_query)):
                pass
            else:
                logger.info(f"Blocked call - research already active (state: {job_manager.state.value})")
                return "I'm already working on research. Please wait for it to complete or ask me to cancel it first."
        
        if not userdata.orchestrator:
            status_handler = StatusHandler(ctx=userdata.ctx, session=self.session)
            status_handler.userdata = userdata
            userdata.status_handler = status_handler
            
            userdata.orchestrator = ResearchOrchestrator(
                ctx=userdata.ctx,
                exa_client=userdata.exa_client,
                llm=self.session.llm,
                status_callback=status_handler.handle_status_update,
                notes_callback=status_handler.handle_notes_update,
                report_callback=status_handler.handle_report_ready,
            )
        
        if job_manager.state == JobState.CLARIFYING:
            if not confirmed and (query is None or query == job_manager.original_query):
                return "I'm waiting for your answer to the clarification question above. Please confirm or provide more details."
            
            if confirmed:
                final_query = query if query and query != job_manager.original_query else job_manager.original_query
            else:
                final_query = query
            
            if not final_query:
                return "I don't have a research query to work with. Please provide a research question."
            
            job_manager.clarified_query = final_query
            request_id = job_manager.request_id or f"research_{int(datetime.now().timestamp())}"
            job_manager.request_id = request_id
            job_manager.state = JobState.BRIEFING
            
            job_manager.task = asyncio.create_task(
                run_research_job(self.session, userdata, userdata.orchestrator, request_id, final_query)
            )
            
            return f"Perfect! Starting deep research on: {final_query}. I'll keep you updated as I make progress!"
        
        if not query:
            return "Please provide a research question or topic to investigate."
        
        job_manager.reset()
        request_id = f"research_{int(datetime.now().timestamp())}"
        job_manager.request_id = request_id
        job_manager.original_query = query
        job_manager.state = JobState.CLARIFYING
        
        try:
            quick_results = await userdata.orchestrator.quick_naive_search(request_id, query, num_results=5)
            job_manager.clarification_results = quick_results
            
            needs_clarification, clarification_message = await userdata.orchestrator.autonomous_clarification(
                request_id,
                query,
                quick_results,
                conversation_history=job_manager.conversation_history
            )
            
            if needs_clarification and clarification_message:
                await send_rpc_to_ui_safe(userdata.ctx, "exa.research/status", {
                    "requestId": request_id,
                    "phase": "clarifying",
                    "title": "Clarification needed",
                    "message": clarification_message,
                    "stats": {},
                    "ts": datetime.now().timestamp(),
                    "clarification": {
                        "question": clarification_message,
                        "originalQuery": query
                    }
                })
                
                return clarification_message
            else:
                job_manager.clarified_query = query
                job_manager.state = JobState.BRIEFING
                
                job_manager.task = asyncio.create_task(
                    run_research_job(self.session, userdata, userdata.orchestrator, request_id, query)
                )
                
                return f"Perfect! I found relevant results. Starting deep research on: {query}. I'll keep you updated as I make progress!"
            
        except Exception as e:
            logger.error(f"Error in quick search or clarification: {e}", exc_info=True)
            job_manager.clarified_query = query
            job_manager.state = JobState.BRIEFING
            
            job_manager.task = asyncio.create_task(
                run_research_job(self.session, userdata, userdata.orchestrator, request_id, query)
            )
            
            return f"Starting deep research on: {query}. I'll keep you updated as I make progress!"
    
    @function_tool()
    async def cancel_research_job(self, context: RunContext[ExaUserData]) -> str:
        """
        Cancel the currently running research job.
        
        Returns:
            Confirmation message
        """
        userdata = context.userdata
        job_manager = userdata.job_manager
        
        if not job_manager or not job_manager.is_active():
            return "There's no research job currently running."
        
        job_manager.cancel()
        
        return f"Canceling the research job. Give me a moment to wrap things up."
    
    @function_tool()
    async def check_research_status(self, context: RunContext[ExaUserData]) -> str:
        """
        Check the status of the current research job.
        
        Call this when the user asks about research progress or status.
        Examples: "how's it going?", "what's the status?", "are you done?"
        
        Returns:
            Current status and progress information
        """
        userdata = context.userdata
        job_manager = userdata.job_manager
        
        if not job_manager or job_manager.state == JobState.IDLE:
            return "No research job is currently running. You can start one by asking me to research a topic!"
        
        state = job_manager.state.value
        progress = job_manager.progress
        
        if job_manager.state == JobState.DONE:
            notes_count = len(job_manager.notes)
            return f"Research completed! I found {notes_count} key insights. The full report is ready on your screen."
        
        if job_manager.state == JobState.CANCELED:
            return "The research job was canceled."
        
        if job_manager.state == JobState.ERROR:
            return "The research job encountered an error and couldn't complete."
        
        status_parts = [f"Research is currently {state}"]
        
        if progress:
            if progress.current_subtopic:
                status_parts.append(f"Working on: {progress.current_subtopic}")
            
            if progress.subtopics_completed > 0:
                total = progress.total_subtopics or "unknown"
                status_parts.append(f"Progress: {progress.subtopics_completed}/{total} subtopics completed")
            
            if progress.sources_found > 0:
                status_parts.append(f"Found {progress.sources_found} sources so far")
        
        return ". ".join(status_parts) + "."
    
    @function_tool()
    async def get_last_report(self, context: RunContext[ExaUserData]) -> str:
        """
        Get the full content of the last completed research report.
        
        Call this when the user asks questions about the research findings,
        wants details from the report, or asks you to explain something from the research.
        
        Examples: "what did you find?", "tell me more about X", "explain the findings"
        
        Returns:
            The full research report content, or a message if no report exists
        """
        userdata = context.userdata
        job_manager = userdata.job_manager
        
        if not job_manager or not job_manager.final_report:
            return "No research report is available yet. I haven't completed any research jobs."
        
        report = job_manager.final_report
        title = job_manager.report_title or "Research Report"
        
        return f"# {title}\n\n{report}"


async def entrypoint(ctx: JobContext):
    """Main entrypoint for the EXA research agent"""
    
    exa_client = EXAClient()
    
    userdata = ExaUserData(
        ctx=ctx,
        exa_client=exa_client,
    )
    
    session = AgentSession[ExaUserData](
        userdata=userdata,
        vad=silero.VAD.load(),
        stt="assemblyai/universal-streaming",
        llm="deepseek-ai/deepseek-v3",
        tts="inworld/inworld-tts-1:Ashley",
        turn_detection=MultilingualModel(),
    )
    
    userdata.session = session
    
    agent = ExaResearchAgent()
    
    await session.start(agent=agent, room=ctx.room, room_input_options=RoomInputOptions(
        noise_cancellation=noise_cancellation.BVC(),
    ))


if __name__ == "__main__":
    agent_name = get_agent_name()
    logger.info(f"Starting agent with name: {agent_name}")
    cli.run_app(WorkerOptions(agent_name=agent_name, entrypoint_fnc=entrypoint))
