"""
RPC communication with UI

This module handles sending RPC messages to the frontend UI,
formatting payloads for status updates, notes, and reports.
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any
from livekit.agents import JobContext

from agent.schemas import ResearchNote

logger = logging.getLogger("rpc-handler")


async def send_rpc_to_ui_safe(ctx: JobContext, method: str, payload: dict) -> None:
    """
    Send RPC message to UI - safe version that works even if session is closed
    
    Args:
        ctx: JobContext with room access
        method: RPC method name (e.g., "exa.research/status")
        payload: Data payload to send
    """
    try:
        room = ctx.room
        remote_participants = list(room.remote_participants.values())
        
        if not remote_participants:
            logger.debug(f"No remote participants, skipping RPC {method}")
            return
        
        client_participant = remote_participants[0]
        
        phase = payload.get("phase", "unknown")
        title = payload.get("title", "unknown")
        request_id = payload.get("requestId", "unknown")
        logger.info(f"Sending RPC [{phase}] {title} (requestId={request_id})")
        
        await room.local_participant.perform_rpc(
            destination_identity=client_participant.identity,
            method=method,
            payload=json.dumps(payload)
        )
        
    except Exception as e:
        logger.error(f"Error sending RPC {method}: {e}", exc_info=True)


async def send_report_via_byte_stream(
    ctx: JobContext,
    request_id: str,
    title: str,
    report: str,
    num_sources: int
) -> None:
    """
    Send report via byte stream instead of RPC (for large payloads)
    
    Args:
        ctx: JobContext with room access
        request_id: Request identifier
        title: Report title
        report: Full report content
        num_sources: Number of unique sources cited
    """
    try:
        room = ctx.room
        remote_participants = list(room.remote_participants.values())
        
        if not remote_participants:
            logger.debug(f"No remote participants, skipping report byte stream")
            return
        
        client_participant = remote_participants[0]
        
        report_data = {
            "requestId": request_id,
            "phase": "reporting",
            "title": "Report complete",
            "message": f"Final report ready: {title}",
            "stats": {"numSources": num_sources},
            "ts": datetime.now().timestamp(),
            "report": {
                "title": title,
                "content": report,
                "sizeBytes": len(report.encode('utf-8')),
                "numSources": num_sources
            }
        }
        
        report_json = json.dumps(report_data)
        report_bytes = report_json.encode('utf-8')
        
        logger.info(f"Streaming report via byte stream: {title}, {len(report_bytes)} bytes, {num_sources} sources")
        
        writer = await room.local_participant.stream_bytes(
            name="report.json",
            total_size=len(report_bytes),
            mime_type="application/json",
            topic="exa_research_report",
            destination_identities=[client_participant.identity],
            attributes={
                "requestId": request_id,
                "title": title,
                "numSources": str(num_sources),
                "type": "research_report"
            },
        )
        
        await writer.write(report_bytes)
        await writer.aclose()
        
        logger.info(f"Report byte stream sent successfully: {title}")
        
    except Exception as e:
        logger.error(f"Error sending report via byte stream: {e}", exc_info=True)


def format_status_payload(
    request_id: str,
    phase: str,
    title: str,
    message: str,
    stats: Dict[str, Any]
) -> dict:
    """
    Format status update payload for RPC
    
    Args:
        request_id: Request identifier
        phase: Current phase (e.g., "briefing", "researching")
        title: Status title
        message: Status message
        stats: Additional statistics dictionary
        
    Returns:
        Formatted payload dict
    """
    return {
        "requestId": request_id,
        "phase": phase,
        "title": title,
        "message": message,
        "stats": stats,
        "ts": datetime.now().timestamp()
    }


def format_notes_payload(request_id: str, note: ResearchNote) -> dict:
    """
    Format research note payload for RPC
    
    Args:
        request_id: Request identifier
        note: ResearchNote to format
        
    Returns:
        Formatted payload dict
    """
    citations_data = [
        {
            "id": c.id,
            "url": c.url,
            "title": c.title,
            "quote": c.quote,
            "publishedAt": c.published_at
        }
        for c in note.citations
    ]
    
    return {
        "requestId": request_id,
        "phase": "researching",
        "title": "Research note complete",
        "message": f"Completed research on: {note.subtopic}",
        "stats": {
            "subtopic": note.subtopic,
            "numCitations": len(citations_data)
        },
        "ts": datetime.now().timestamp(),
        "note": {
            "subtopic": note.subtopic,
            "summaryMarkdown": note.summary_markdown,
            "citations": citations_data
        }
    }


def format_report_payload(
    request_id: str,
    title: str,
    report: str,
    num_sources: int
) -> dict:
    """
    Format final report payload for RPC
    
    Args:
        request_id: Request identifier
        title: Report title
        report: Full report content
        num_sources: Number of unique sources cited
        
    Returns:
        Formatted payload dict
    """
    report_size_bytes = len(report.encode('utf-8'))
    
    return {
        "requestId": request_id,
        "phase": "reporting",
        "title": "Report complete",
        "message": f"Final report ready: {title}",
        "stats": {"numSources": num_sources},
        "ts": datetime.now().timestamp(),
        "report": {
            "title": title,
            "content": report,
            "sizeBytes": report_size_bytes,
            "numSources": num_sources
        }
    }

