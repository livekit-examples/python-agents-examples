"""
Voice synthesis for reports

This module handles speaking the final research report to the user,
including truncation and natural delivery.
"""
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from livekit.agents import AgentSession

logger = logging.getLogger("voice-speaker")


def truncate_for_speech(report: str, max_chars: int = 4500) -> str:
    """
    Truncate report if too long for voice synthesis
    
    Estimates ~150 words per minute, so ~750 words for 5 minutes = ~4500 chars.
    Tries to find a natural breaking point (sentence or paragraph end).
    
    Args:
        report: Full report text
        max_chars: Maximum characters to include (default: 4500)
        
    Returns:
        Truncated report text with continuation notice if truncated
    """
    if len(report) <= max_chars:
        return report
    
    truncated = report[:max_chars]
    last_period = truncated.rfind('.')
    last_newline = truncated.rfind('\n')
    cut_point = max(last_period, last_newline)
    
    if cut_point > max_chars * 0.8:
        truncated = truncated[:cut_point + 1]
    
    return truncated + "\n\n[The full report continues in your on-screen document...]"


async def speak_final_report(session: 'AgentSession', title: str, report: str):
    """
    Read the final report immediately after research completes
    
    This function creates a natural-sounding voice presentation of the research
    findings, truncating if necessary to keep it to a reasonable length.
    
    Args:
        session: AgentSession for voice generation
        title: Report title
        report: Full report content
    """
    try:
        _ = session.userdata
        
        report_text = truncate_for_speech(report)
        
        user_input = f"""Read this research report to the user naturally and conversationally. 

Report Title: {title}

Report Content:
{report_text}

Instructions:
- Read it in a clear, engaging way
- Pause briefly between major sections
- If the report was truncated, mention that the full version is available on screen
- Sound like you're presenting findings, not just reading text
- Keep a natural pace"""

        await session.generate_reply(user_input=user_input, allow_interruptions=True)
        
    except (RuntimeError, AttributeError) as e:
        logger.debug(f"Session closed, skipping final report voice reading: {e}")
    except Exception as e:
        logger.error(f"Error reading final report: {e}", exc_info=True)
        try:
            if hasattr(session, '_closed') and not session._closed:
                session.say(f"Research complete! The full report on {title} is available on your screen.")
        except:
            pass

