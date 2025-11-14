"""
Status queue management for voice updates

This module manages a queue of status updates that need to be spoken to the user,
processing them sequentially with natural language generation.
"""
import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from livekit.agents import AgentSession

logger = logging.getLogger("status-queue")


class StatusQueue:
    """
    Manages queued status updates for voice synthesis
    
    This class processes status updates one by one, using the LLM to generate
    natural-sounding voice updates from the raw status messages.
    """
    
    def __init__(self, session: 'AgentSession', userdata):
        """
        Initialize status queue
        
        Args:
            session: AgentSession for generating voice replies
            userdata: ExaUserData containing the queue
        """
        self.session = session
        self.userdata = userdata
    
    def start_processing(self) -> asyncio.Task:
        """
        Start processing the status queue
        
        Returns:
            Asyncio task for the processing loop
        """
        return asyncio.create_task(self.process_queue())
    
    async def process_queue(self):
        """
        Process queued status updates one by one
        
        This method runs in the background, pulling status updates from the queue
        and generating natural voice updates using the LLM.
        """
        try:
            while self.userdata.status_queue:
                try:
                    _ = self.session.userdata
                except (RuntimeError, AttributeError):
                    logger.debug("Session closed, clearing status queue")
                    self.userdata.status_queue.clear()
                    break
                
                status = self.userdata.status_queue.pop(0)
                phase = status["phase"]
                title = status.get("title", "")
                message = status["message"]
                
                # Generate natural-sounding status update
                # The message already contains context like subtopic names, so use it naturally
                user_input = f"""Generate a brief, natural spoken status update (one sentence, max 10 seconds when spoken).

Current activity: {title}
Details: {message}

Make it conversational and friendly. Don't be robotic. Examples:
- Good: "I'm investigating the company's funding history and found 8 relevant articles."
- Good: "I'm analyzing sources about the founder's background."
- Bad: "Synthesizing findings for subtopic 1"
- Bad: "Currently researching subtopic 2"

Generate the update:"""
                
                try:
                    await self.session.generate_reply(user_input=user_input, allow_interruptions=True)
                except (RuntimeError, AttributeError):
                    logger.debug("Session closed during status queue processing")
                    self.userdata.status_queue.clear()
                    break
                
                await asyncio.sleep(1.0)
                
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Error processing status queue: {e}")
        finally:
            self.userdata.status_task = None
    
    async def clear(self):
        """
        Clear the status queue and cancel any ongoing processing
        """
        try:
            if self.userdata.status_task and not self.userdata.status_task.done():
                self.userdata.status_task.cancel()
                try:
                    await self.userdata.status_task
                except asyncio.CancelledError:
                    pass
            
            self.userdata.status_queue.clear()
            self.userdata.status_task = None
            
        except Exception as e:
            logger.error(f"Error clearing status queue: {e}")

