"""
Source synthesis and findings generation

This module handles synthesizing findings from multiple sources
into coherent research notes with citations.
"""
import logging
from typing import List, Optional
from datetime import datetime

from agent.schemas import ResearchNote, Citation, EXAContent
from agent.utils import execute_llm_chat, build_research_context
from agent.prompts import researcher_prompt

logger = logging.getLogger("synthesizer")


async def synthesize_findings(
    llm,
    subtopic: str,
    sources: List[EXAContent],
    original_query: str = "",
    research_brief: str = "",
    conversation_history: Optional[list] = None
) -> ResearchNote:
    """
    Synthesize findings from sources into a research note
    
    Args:
        llm: LLM instance for synthesis
        subtopic: Current subtopic being researched
        sources: List of content results from EXA
        original_query: Original user query for context
        research_brief: Full research brief for context
        conversation_history: Optional conversation context
        
    Returns:
        ResearchNote with summary and citations
    """
    if not sources:
        logger.warning(f"No sources provided for subtopic: {subtopic}")
        return ResearchNote(
            subtopic=subtopic,
            summary_markdown=f"No sources found for: {subtopic}",
            citations=[],
            timestamp=datetime.now()
        )
    
    sources_with_numbers = ""
    for idx, source in enumerate(sources, 1):
        content = source.text or source.summary or "(No content available)"
        sources_with_numbers += f"\n\n---\n\n**[{idx}] {source.title}**\nURL: {source.url}\n\n{content}"
    
    if not sources_with_numbers.strip():
        logger.warning(f"No content extracted from {len(sources)} sources")
        return ResearchNote(
            subtopic=subtopic,
            summary_markdown=f"No content could be extracted from {len(sources)} sources",
            citations=[],
            timestamp=datetime.now()
        )
    
    context_info = build_research_context(original_query, research_brief)
    
    response = await execute_llm_chat(
        llm=llm,
        system_prompt=researcher_prompt(original_query=original_query, research_brief=research_brief),
        user_prompt=f"""Current Subtopic to Research: {subtopic}
{context_info}

Sources Found (use these numbers for citations):
{sources_with_numbers}

**IMPORTANT INSTRUCTIONS**:
1. **FIRST: Validate each source** - Check if the source is about the CORRECT entity/subject from the research goal:
   - If researching "Tesla Inc." (the car company founded 2003), REJECT sources about "Nikola Tesla" (the inventor from 1800s-1900s)
   - If researching a company, REJECT sources about people with the same name
   - If researching a person, REJECT sources about companies/products with the same name
   - Check dates, context, and content to ensure sources match the research subject
2. Write a comprehensive markdown summary about "{subtopic}" using ONLY relevant, validated sources
3. If most/all sources are about the WRONG entity, acknowledge this: "Sources found were primarily about [wrong entity] rather than [correct entity]. Limited/no relevant information available."
4. Reference sources using inline citations: [1], [2], [3], etc.
5. You can reference multiple sources like [1][2] or [1,3,5]
6. Do NOT invent information not in the sources
7. Do NOT return a JSON object - just return the markdown summary text
8. Include specific facts, quotes, and data from validated sources
9. Make the summary relevant to both this subtopic AND the overall research goal

Example format:
Tesla was founded in 2003 by Martin Eberhard and Marc Tarpenning [1]. Elon Musk joined as chairman and investor in 2004 [2]. The company's first vehicle, the Roadster, was released in 2008 [1][3].

Now write your summary:""",
        parse_json=False,
        extract_json=False,
        conversation_history=conversation_history
    )
    
    summary = str(response).strip()
    
    if not summary:
        summary = f"Could not generate summary for: {subtopic}"
    
    citations = [
        Citation(
            id=source.id,
            url=source.url,
            title=source.title,
            quote=(source.text or source.summary or "")[:600],
            published_at=None
        )
        for source in sources
    ]
    
    note = ResearchNote(
        subtopic=subtopic,
        summary_markdown=summary,
        citations=citations,
        timestamp=datetime.now()
    )
    
    logger.info(f"Synthesized note for '{subtopic}' with {len(citations)} citations")
    
    return note

