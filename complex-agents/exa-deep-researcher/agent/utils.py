"""
Utility functions for EXA Deep Researcher
"""
import json
import asyncio
import logging
import re
from typing import Optional, Any, Union, List
from livekit.agents.llm import ChatContext, ChatMessage

logger = logging.getLogger("exa-utils")


async def execute_llm_chat(
    llm,
    system_prompt: str,
    user_prompt: str,
    parse_json: bool = False,
    extract_json: bool = False,
    conversation_history: Optional[list] = None,
) -> Union[str, dict, list]:
    """
    Centralized LLM chat execution with response parsing
    
    Args:
        llm: The LLM instance to use
        system_prompt: System message defining behavior
        user_prompt: User message with the task
        parse_json: If True, parse response as JSON
        extract_json: If True and parse fails, try to extract JSON from response
        
    Returns:
        String response, or parsed JSON if parse_json=True
    """
    messages = [ChatMessage(type="message", role="system", content=[system_prompt])]
    
    if conversation_history:
        recent_history = conversation_history[-10:]
        for msg in recent_history:
            messages.append(msg)
    
    messages.append(ChatMessage(type="message", role="user", content=[user_prompt]))
    
    chat_ctx = ChatContext(messages)
    
    response = ""
    chunk_count = 0
    non_empty_chunks = 0
    
    try:
        async with llm.chat(chat_ctx=chat_ctx) as stream:
            async for chunk in stream:
                chunk_count += 1
                if chunk is None:
                    continue
                
                content = getattr(chunk.delta, 'content', None) if hasattr(chunk, 'delta') else str(chunk)
                
                if content is not None:
                    if content.strip():
                        non_empty_chunks += 1
                    response += content
                    
    except Exception as e:
        logger.error(f"Error streaming LLM response: {e}", exc_info=True)
        raise
    
    response = response.strip()
    
    if not response:
        logger.warning(
            f"LLM returned empty response. "
            f"Total chunks: {chunk_count}, Non-empty chunks: {non_empty_chunks}, "
            f"parse_json={parse_json}, extract_json={extract_json}"
        )
        if parse_json:
            logger.error("Empty response but JSON parsing was requested - this will fail")
    
    if not parse_json:
        return response
    
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        if extract_json:
            import re
            code_block_pattern = r'```(?:json)?\s*\n?(.*?)```'
            matches = re.findall(code_block_pattern, response, re.DOTALL | re.IGNORECASE)
            for match in matches:
                cleaned = match.strip()
                if cleaned.startswith('{') or cleaned.startswith('['):
                    try:
                        return json.loads(cleaned)
                    except json.JSONDecodeError:
                        pass
        
        logger.warning(
            f"Failed to parse JSON from LLM response. "
            f"Response length: {len(response)}, "
            f"Preview: {response[:500]}..."
        )
        return response


async def stream_llm_chat(llm, messages: List[ChatMessage]) -> str:
    """Stream LLM chat from ChatMessage list"""
    chat_ctx = ChatContext(messages)
    response = ""
    async with llm.chat(chat_ctx=chat_ctx) as stream:
        async for chunk in stream:
            if not chunk:
                continue
            content = getattr(chunk.delta, 'content', None) if hasattr(chunk, 'delta') else str(chunk)
            if content:
                response += content
    return response.strip()


def format_note_with_citations(subtopic: str, summary: str, citations) -> str:
    """Format a research note with citations"""
    note_text = f"## {subtopic}\n\n{summary}\n\n"
    if citations:
        note_text += "**Citations:**\n"
        for cit in citations:
            note_text += f"- [{cit.title}]({cit.url})\n"
    return note_text


def build_research_context(original_query: str = "", research_brief: str = "") -> str:
    """Build context info string for research subtopics"""
    if not (original_query or research_brief):
        return ""
    
    context = "\n\nOVERALL RESEARCH CONTEXT:\n"
    if original_query:
        context += f"Original Research Goal: {original_query}\n"
    if research_brief:
        context += f"Research Brief: {research_brief}\n"
    context += "\nRemember: This subtopic is part of a larger research effort. Make sure your findings are relevant to the overall goal.\n"
    return context


def extract_content_from_sources(contents) -> str:
    """Extract text content from EXA contents"""
    return "\n\n---\n\n".join([
        f"Source: {c.title}\nURL: {c.url}\n\n{c.text or c.summary or '(No content)'}"
        for c in contents if c.text or c.summary
    ])


def parse_citations_from_response(citation_data: List[dict]) -> List:
    """Parse citations from LLM response data"""
    from agent.schemas import Citation
    
    return [
        Citation(
            id=str(cit.get("id", "")),
            url=cit.get("url", ""),
            title=cit.get("title", ""),
            quote=cit.get("quote", ""),
            published_at=cit.get("published_at")
        )
        for cit in citation_data
    ]


def parse_json_response_with_fallback(response, fallback_value):
    """Parse JSON response with fallback if not dict"""
    if not isinstance(response, dict):
        return fallback_value
    return response


async def fetch_contents_in_batches(exa_client, urls, content_options, max_concurrent: int = 3):
    """Fetch EXA contents in batches to respect concurrency limits"""
    all_contents = []
    for i in range(0, len(urls), max_concurrent):
        batch_urls = urls[i:i + max_concurrent]
        contents = await exa_client.get_contents(batch_urls, content_options)
        all_contents.extend(contents)
        if i + max_concurrent < len(urls):
            await asyncio.sleep(0.5)
    return all_contents


def format_findings_for_report(notes) -> str:
    """
    Format research notes with global citation numbering
    
    This remaps local [1], [2], [3] in each section to global [1]-[N]
    so the LLM sees consistent citation numbers across all sections.
    """
    global_sources = []
    url_to_global_idx = {}
    
    for note in notes:
        for citation in note.citations:
            if citation.url not in url_to_global_idx:
                url_to_global_idx[citation.url] = len(global_sources) + 1
                global_sources.append(citation)
    
    formatted_sections = []
    
    for note in notes:
        local_to_global = {}
        for local_idx, citation in enumerate(note.citations, 1):
            global_idx = url_to_global_idx.get(citation.url)
            if global_idx:
                local_to_global[local_idx] = global_idx
        
        summary = note.summary_markdown
        for local_idx, global_idx in sorted(local_to_global.items(), reverse=True):
            summary = re.sub(rf'\[{local_idx}\]', f'[{global_idx}]', summary)
        
        formatted_sections.append(f"### {note.subtopic}\n\n{summary}\n\n")
    
    return "\n\n".join(formatted_sections)
