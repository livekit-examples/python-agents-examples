"""
Job Manager for managing research job state and lifecycle

The JobManager maintains the state of a single active research job,
including progress tracking, notes collection, and lifecycle management.
"""
import asyncio
from typing import Optional, List, Dict, Callable
from dataclasses import dataclass, field

from agent.schemas import JobState, JobProgress, ResearchNote, EXAResult


@dataclass
class JobManager:
    """Manages a single active research job"""
    request_id: Optional[str] = None
    state: JobState = JobState.IDLE
    progress: Optional[JobProgress] = None
    notes: List[ResearchNote] = field(default_factory=list)
    research_brief: str = ""
    report_title: str = ""
    final_report: str = ""
    cancel_requested: bool = False
    task: Optional[asyncio.Task] = None
    
    # Source content cache
    source_cache: Dict[str, str] = field(default_factory=dict)
    
    # Clarification support
    original_query: str = ""
    clarification_results: List[EXAResult] = field(default_factory=list)
    clarified_query: Optional[str] = None
    clarification_event: Optional[asyncio.Event] = None
    clarification_callback: Optional[Callable] = None
    
    # Conversation history for context
    conversation_history: List = field(default_factory=list)
    
    def is_active(self) -> bool:
        """Check if a job is currently active (including initialization)"""
        return self.state not in [JobState.IDLE, JobState.DONE, JobState.CANCELED, JobState.ERROR]
    
    def cancel(self):
        """Request cancellation of the current job"""
        self.cancel_requested = True
        if self.task and not self.task.done():
            self.task.cancel()
    
    def reset(self):
        """Reset to idle state"""
        self.request_id = None
        self.state = JobState.IDLE
        self.progress = None
        self.notes = []
        self.research_brief = ""
        self.report_title = ""
        self.final_report = ""
        self.cancel_requested = False
        self.task = None
        self.source_cache = {}
        self.original_query = ""
        self.clarification_results = []
        self.clarified_query = None
        self.clarification_event = None
        self.clarification_callback = None

