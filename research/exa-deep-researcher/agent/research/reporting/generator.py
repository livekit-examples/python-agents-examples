"""
Final report generation

This module generates comprehensive research reports from
accumulated research notes and findings.
"""
import logging
from typing import List, Optional, Callable

from agent.schemas import ResearchNote
from agent.utils import execute_llm_chat, format_findings_for_report
from agent.prompts import final_report_generation_prompt, get_today_str

logger = logging.getLogger("report-generator")


async def generate_report(
    llm,
    request_id: str,
    title: str,
    brief: str,
    notes: List[ResearchNote],
    status_callback: Optional[Callable] = None,
    report_callback: Optional[Callable] = None
) -> str:
    """
    Generate final research report
    
    Args:
        llm: LLM instance for report generation
        request_id: Request identifier
        title: Report title
        brief: Research brief with context
        notes: List of research notes to synthesize
        status_callback: Optional callback for status updates
        report_callback: Optional callback when report is complete
        
    Returns:
        Final report as markdown string
    """
    if status_callback:
        await status_callback(
            request_id,
            "reporting",
            "Writing final report",
            f"Compiling all findings into a comprehensive report on: {title}",
            {"title": title}
        )
    
    # Collect global sources first (must match the order in format_findings_for_report)
    global_sources = []
    seen_urls = set()
    for note in notes:
        for citation in note.citations:
            if citation.url and citation.url not in seen_urls:
                seen_urls.add(citation.url)
                global_sources.append(citation)
    
    findings = format_findings_for_report(notes)
    
    report_prompt = final_report_generation_prompt(
        research_brief=brief,
        date=get_today_str(),
        findings=findings
    )
    
    logger.info(f"Generating final report: {title}")
    
    report = await execute_llm_chat(
        llm=llm,
        system_prompt="",
        user_prompt=report_prompt,
        conversation_history=None
    )
    
    report = str(report).strip()
    
    if global_sources:
        if "### Sources" not in report and "## Sources" not in report:
            report += "\n\n### Sources\n\n"
            for idx, citation in enumerate(global_sources, 1):
                report += f"[{idx}] {citation.title}: {citation.url}\n"
    
    num_unique_sources = len(global_sources)
    logger.info(f"Generated report: {title} ({len(report)} chars, {num_unique_sources} sources)")
    
    if report_callback:
        await report_callback(request_id, title, report, num_unique_sources)
    
    return report

