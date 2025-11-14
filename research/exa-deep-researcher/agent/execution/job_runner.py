"""
Research job execution coordination

This module coordinates the execution of research jobs, managing the
workflow from briefing through research to final report generation.
"""
import asyncio
import logging
from typing import TYPE_CHECKING

from schemas import JobState
from agent.storage.reports import save_report
from agent.voice.speaker import speak_final_report
from agent.voice.queue import StatusQueue

if TYPE_CHECKING:
    from livekit.agents import AgentSession

logger = logging.getLogger("job-runner")


async def run_research_job(
    session: 'AgentSession',
    userdata,
    orchestrator,
    request_id: str,
    query: str
):
    """
    Run the complete research workflow in background
    
    This function coordinates all phases of research:
    1. Write brief (plan research)
    2. Iterative research (supervisor pattern)
    3. Generate final report
    4. Save to disk
    5. Speak final report
    
    Args:
        session: AgentSession for voice updates
        userdata: ExaUserData with job manager
        orchestrator: ResearchOrchestrator for research execution
        request_id: Request identifier
        query: Research query
    """
    job_manager = userdata.job_manager
    
    try:
        brief, title, subtopics = await orchestrator.write_brief(
            request_id, 
            query,
            conversation_history=job_manager.conversation_history
        )
        job_manager.research_brief = brief
        job_manager.report_title = title
        job_manager.state = JobState.RESEARCHING
        
        original_query = job_manager.original_query or query
        notes = await orchestrator.iterative_supervise(
            request_id,
            brief,
            original_query,
            planned_subtopics=subtopics,
            conversation_history=job_manager.conversation_history
        )
        
        for note in notes:
            job_manager.notes.append(note)
        
        job_manager.state = JobState.REPORTING
        final_report = await orchestrator.generate_final_report(
            request_id, title, brief, notes
        )
        job_manager.final_report = final_report
        
        await save_report(title, final_report)
        
        job_manager.state = JobState.DONE
        
        if userdata.status_task and not userdata.status_task.done():
            userdata.status_task.cancel()
            try:
                await userdata.status_task
            except asyncio.CancelledError:
                pass
        userdata.status_queue.clear()
        
        await speak_final_report(session, title, final_report)
        
    except asyncio.CancelledError:
        job_manager.state = JobState.CANCELED
        try:
            session.say("Research was canceled.")
        except (RuntimeError, AttributeError):
            pass
    except Exception as e:
        logger.error(f"Research job error: {e}", exc_info=True)
        job_manager.state = JobState.ERROR
        try:
            session.say(f"Sorry, I encountered an error during research: {str(e)[:100]}")
        except (RuntimeError, AttributeError):
            pass

