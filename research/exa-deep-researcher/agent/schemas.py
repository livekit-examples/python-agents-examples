"""
Data schemas for EXA Deep Researcher agent
"""
from typing import Optional, List, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


# Job State Machine
class JobState(str, Enum):
    IDLE = "idle"
    CLARIFYING = "clarifying"
    BRIEFING = "briefing"
    RESEARCHING = "researching"
    COMPRESSING = "compressing"
    REPORTING = "reporting"
    DONE = "done"
    CANCELED = "canceled"
    ERROR = "error"


# EXA API Parameters
class EXASearchParams(BaseModel):
    """Parameters for EXA search API"""
    query: str
    search_type: Optional[Literal["auto", "keyword", "neural"]] = "auto"
    result_category: Optional[str] = None
    country: Optional[str] = None
    num_results: Optional[int] = 10
    
    # Date filters
    start_published_date: Optional[str] = None  # ISO format
    end_published_date: Optional[str] = None
    start_crawl_date: Optional[str] = None
    end_crawl_date: Optional[str] = None
    
    # Domain filters
    include_domains: Optional[List[str]] = None
    exclude_domains: Optional[List[str]] = None
    
    # Text filters
    include_text: Optional[str] = None  # exact phrase, 5 words max
    exclude_text: Optional[str] = None
    
    # Advanced options
    use_autoprompt: Optional[bool] = None  # Not supported in all EXA SDK versions


class EXAContentOptions(BaseModel):
    """Options for EXA contents API"""
    text: Optional[bool] = True  # Get full text
    highlights: Optional[bool] = False
    summary: Optional[bool] = False
    
    # Livecrawl options
    livecrawl: Optional[Literal["always", "fallback", "never"]] = "fallback"
    livecrawl_timeout: Optional[int] = 5000  # milliseconds
    
    # Content format
    max_characters: Optional[int] = None
    include_html_tags: Optional[bool] = False
    subpages: Optional[int] = None  # Include subpages
    subpage_target: Optional[str] = None


# EXA API Response Models
class EXAResult(BaseModel):
    """Single search result from EXA"""
    id: str
    url: str
    title: str
    score: Optional[float] = None
    published_date: Optional[str] = None
    author: Optional[str] = None


class EXAContent(BaseModel):
    """Content fetched from EXA"""
    id: str
    url: str
    title: str
    text: Optional[str] = None
    highlights: Optional[List[str]] = None
    summary: Optional[str] = None


# Research Job Models
class Citation(BaseModel):
    """A citation with quote and metadata"""
    id: str
    url: str
    title: str
    quote: str
    published_at: Optional[str] = None


class ResearchNote(BaseModel):
    """Notes for a research subtopic"""
    subtopic: str
    summary_markdown: str
    citations: List[Citation]
    timestamp: datetime


class JobProgress(BaseModel):
    """Progress tracking for a research job"""
    request_id: str
    state: JobState
    phase: str
    title: str
    message: str
    progress_pct: Optional[float] = None
    stats: dict = Field(default_factory=dict)
    timestamp: datetime

