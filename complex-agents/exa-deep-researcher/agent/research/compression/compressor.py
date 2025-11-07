"""
Note compression for token management

This module handles compressing accumulated research notes to manage
token usage in subsequent LLM calls during long research sessions.
"""
import logging
from typing import List, Optional, Callable

from livekit.agents.llm import ChatMessage
from agent.schemas import ResearchNote
from agent.utils import stream_llm_chat, format_note_with_citations
from agent.prompts import compress_research_system_prompt, compress_research_simple_human_message, get_today_str

logger = logging.getLogger("compressor")


async def compress_notes(
    llm,
    request_id: str,
    notes: List[ResearchNote],
    status_callback: Optional[Callable] = None
) -> str:
    """
    Compress accumulated notes to manage token usage
    
    As we accumulate research notes, the context grows. This function uses an LLM
    to compress/consolidate multiple notes into a more concise format while preserving
    key information. This helps manage token limits in subsequent LLM calls.
    
    Called periodically during research (when 4+ notes are collected).
    
    Args:
        llm: LLM instance for compression
        request_id: Request identifier
        notes: List of research notes to compress
        status_callback: Optional callback for status updates
        
    Returns:
        Compressed notes as markdown string (streamed from LLM)
    """
    if not notes:
        return ""
    
    if status_callback:
        await status_callback(
            request_id,
            "compressing",
            "Organizing findings",
            f"Consolidating {len(notes)} research topics to keep everything organized",
            {"notes_count": len(notes)}
        )
    
    messages = [
        ChatMessage(type="message", role="system", content=[compress_research_system_prompt(get_today_str())])
    ]
    
    for note in notes:
        messages.append(
            ChatMessage(
                type="message",
                role="assistant",
                content=[format_note_with_citations(note.subtopic, note.summary_markdown, note.citations)]
            )
        )
    
    messages.append(
        ChatMessage(type="message", role="user", content=[compress_research_simple_human_message])
    )
    
    logger.info(f"Compressing {len(notes)} notes")
    
    compressed = await stream_llm_chat(llm, messages)
    
    logger.info(f"Compressed {len(notes)} notes into {len(compressed)} chars")
    
    return compressed

