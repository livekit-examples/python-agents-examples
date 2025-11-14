"""
Status, notes, and report update handling

This module provides a StatusHandler class that processes callbacks
from the orchestrator and formats them for RPC communication and voice updates.
"""
import logging
from typing import Optional
from agent.schemas import ResearchNote
from .rpc import send_rpc_to_ui_safe, format_status_payload, format_notes_payload, format_report_payload, send_report_via_byte_stream
from agent.voice.queue import StatusQueue
from livekit.agents import AgentSession

logger = logging.getLogger("status-handler")


class StatusHandler:
    """
    Handles status updates, notes, and report callbacks from orchestrator
    
    This class serves as the bridge between the orchestrator's research workflow
    and the agent's UI/voice systems. It formats and dispatches updates appropriately.
    """
    
    def __init__(self, ctx, session: Optional['AgentSession'] = None):
        """
        Initialize status handler
        
        Args:
            ctx: JobContext for RPC communication
            session: Optional AgentSession for voice updates
        """
        self.ctx = ctx
        self.session = session
        self.userdata = None
    
    async def handle_status_update(
        self,
        request_id: str,
        phase: str,
        title: str,
        message: str,
        stats: dict
    ):
        """
        Handle status updates from orchestrator
        
        Sends status to UI via RPC and queues voice update if session is available.
        
        Args:
            request_id: Request identifier
            phase: Current phase (e.g., "briefing", "researching")
            title: Status title
            message: Status message
            stats: Additional statistics
        """
        try:
            payload = format_status_payload(request_id, phase, title, message, stats)
            await send_rpc_to_ui_safe(self.ctx, "exa.research/status", payload)
            
            if self.session and self.userdata:
                try:
                    await self._speak_status_update(phase, message, title)
                except (RuntimeError, AttributeError):
                    logger.debug("Session closed, skipping voice update")
        except Exception as e:
            logger.error(f"Error handling status update: {e}")
    
    async def handle_notes_update(self, request_id: str, note: ResearchNote):
        """
        Handle research notes from orchestrator
        
        Formats note with citations and sends to UI.
        
        Args:
            request_id: Request identifier
            note: ResearchNote with findings and citations
        """
        try:
            payload = format_notes_payload(request_id, note)
            await send_rpc_to_ui_safe(self.ctx, "exa.research/status", payload)
        except Exception as e:
            logger.error(f"Error handling notes update: {e}")
    
    async def handle_report_ready(
        self,
        request_id: str,
        title: str,
        report: str,
        num_sources: int
    ):
        """
        Handle report ready notification
        
        Sends report to UI via byte stream (for large payloads).
        Also sends a lightweight status update via RPC to notify the UI.
        
        Args:
            request_id: Request identifier
            title: Report title
            report: Full report content
            num_sources: Number of unique sources cited
        """
        try:
            report_size_mb = len(report.encode('utf-8')) / (1024 * 1024)
            logger.info(f"Preparing report byte stream: {title}, {len(report)} chars, {report_size_mb:.2f}MB, {num_sources} sources")
            
            status_payload = format_status_payload(
                request_id,
                "reporting",
                "Report complete",
                f"Final report ready: {title}",
                {"numSources": num_sources}
            )
            await send_rpc_to_ui_safe(self.ctx, "exa.research/status", status_payload)
            
            await send_report_via_byte_stream(self.ctx, request_id, title, report, num_sources)
            
            logger.info(f"Report byte stream sent successfully: {title}")
        except Exception as e:
            logger.error(f"Failed to send report byte stream: {e}", exc_info=True)
    
    async def _speak_status_update(self, phase: str, message: str, title: str = None):
        """
        Queue a status update for speaking
        
        This is called internally when a status update should be voiced.
        The actual queuing logic is handled by the voice module.
        
        Args:
            phase: Current phase
            message: Status message
            title: Optional status title
        """
        try:
            if not self.userdata:
                return
            
            title_to_check = title or phase
            should_speak = False
            
            if phase == "researching" and "Starting research" in title_to_check:
                should_speak = True
            elif phase == "reporting":
                should_speak = True
            
            if not should_speak:
                logger.debug(f"Skipping voice update for phase={phase}, title={title_to_check}")
                return
                
            self.userdata.status_queue.append({
                "phase": phase,
                "message": message,
                "title": title or phase
            })
            if not self.userdata.status_task or self.userdata.status_task.done():
                status_queue = StatusQueue(self.session, self.userdata)
                self.userdata.status_task = status_queue.start_processing()
                
        except Exception as e:
            logger.error(f"Error queuing status update: {e}")

