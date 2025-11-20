"""
Research orchestrator for managing background research jobs

This module coordinates the deep research workflow using components
from the research/ package.
"""
import os
import asyncio
import logging
from typing import Optional, List, Dict, Callable

from livekit.agents import JobContext
from livekit.agents.llm import LLM

from agent.schemas import JobState, ResearchNote, EXAResult
from agent.exa_client import EXAClient
from agent.prompts import brief_generation_prompt, lead_researcher_prompt, get_today_str
from agent.utils import execute_llm_chat, parse_json_response_with_fallback

# Research components
from agent.research.clarification.search import quick_search
from agent.research.clarification.analyzer import AutonomousClarification
from agent.research.engine.subtopic import ResearchSubtopic
from agent.research.compression.compressor import compress_notes
from agent.research.reporting.generator import generate_report

logger = logging.getLogger("research-orchestrator")
logger.setLevel(logging.INFO)


class ResearchOrchestrator:
    """
    Orchestrates the deep research workflow
    
    This class manages the entire research process by coordinating
    components from the research/ package:
    1. Clarification (optional) - asks user to clarify ambiguous queries
    2. Briefing - creates a research plan from the query
    3. Research Loop - iteratively researches topics until comprehensive
    4. Compression - periodically compresses notes to manage tokens (when 4+ notes)
    5. Reporting - generates final comprehensive report
    
    The research uses an "iterative supervisor" pattern where an LLM supervisor
    evaluates findings after each iteration and decides what to research next.
    """
    
    def __init__(
        self,
        ctx: JobContext,
        exa_client: EXAClient,
        llm: LLM,
        status_callback: Optional[Callable] = None,
        notes_callback: Optional[Callable] = None,
        report_callback: Optional[Callable] = None,
    ):
        self.ctx = ctx
        self.exa_client = exa_client
        self.llm = llm
        self.status_callback = status_callback
        self.notes_callback = notes_callback
        self.report_callback = report_callback
        
        self.max_iterations = int(os.environ.get("EXA_MAX_ITERATIONS", "4"))
        self.max_results_per_search = int(os.environ.get("EXA_DEFAULT_MAX_RESULTS", "10"))
        self.max_concurrent_fetches = int(os.environ.get("EXA_MAX_CONCURRENT_FETCHES", "3"))
        self.max_concurrent_research_units = int(os.environ.get("EXA_MAX_CONCURRENT_RESEARCH_UNITS", "3"))
        
        # Initialize research components
        self.clarification_analyzer = AutonomousClarification(llm=self.llm)
        self.subtopic_researcher = ResearchSubtopic(
            exa_client=self.exa_client,
            llm=self.llm,
            max_results_per_search=self.max_results_per_search,
            max_concurrent_fetches=self.max_concurrent_fetches,
            status_callback=self.status_callback,
            notes_callback=self.notes_callback
        )
    
    async def _send_status(self, request_id: str, phase: str, title: str, message: str, stats: Dict = None):
        """Send status update"""
        if self.status_callback:
            await self.status_callback(request_id, phase, title, message, stats or {})
        if phase in ["briefing", "researching", "compressing", "reporting"]:
            logger.info(f"[{phase.upper()}] {title}")
    
    async def quick_naive_search(self, request_id: str, query: str, num_results: int = 5) -> List[EXAResult]:
        """
        Perform a quick naive search to get initial results for clarification
        
        Returns:
            List of search results (typically 3-5 results)
        """
        return await quick_search(
            exa_client=self.exa_client,
            request_id=request_id,
            query=query,
            num_results=num_results,
            status_callback=self.status_callback
        )
    
    async def autonomous_clarification(
        self,
        request_id: str,
        query: str,
        results: List[EXAResult],
        conversation_history: Optional[list] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Autonomously determine if clarification is needed based on search results
        
        Returns:
            (needs_clarification: bool, clarification_message: Optional[str])
        """
        return await self.clarification_analyzer.analyze(
            query=query,
            results=results,
            conversation_history=conversation_history
        )
    
    async def write_brief(self, request_id: str, query: str, conversation_history: Optional[list] = None) -> tuple[str, str, List[str]]:
        """
        Generate research brief, title, and subtopics
        
        Takes the user's query and creates a focused research brief that will guide
        the entire research process.
        
        Returns:
            (brief, title, subtopics) tuple
        """
        logger.info(f"[BRIEFING] Creating research plan for: {query} (requestId={request_id})")
        await self._send_status(request_id, "briefing", "Planning research", f"Creating research plan for: {query}", {})
        
        response = await execute_llm_chat(
            llm=self.llm,
            system_prompt=brief_generation_prompt(query),
            user_prompt=f"Create a focused research brief and title for: {query}",
            parse_json=True,
            extract_json=True,
            conversation_history=conversation_history
        )
        
        if isinstance(response, dict):
            brief = response.get("brief", query)
            title = response.get("title", f"Research: {query[:50]}")
            subtopics = response.get("subtopics", [])
            if not isinstance(subtopics, list):
                subtopics = []
        else:
            brief = str(response) or query
            title = f"Research: {query[:50]}"
            subtopics = []
        
        logger.info(f"Generated brief: {title} with {len(subtopics)} subtopics")
        
        await self._send_status(request_id, "briefing", title, f"Research plan ready: {title}", {})
        
        return brief, title, subtopics
    
    async def iterative_supervise(
        self,
        request_id: str,
        brief: str,
        original_query: str,
        planned_subtopics: Optional[List[str]] = None,
        conversation_history: Optional[list] = None
    ) -> List[ResearchNote]:
        """
        Iterative supervisor pattern: evaluates findings and dynamically decides what to research next.
        
        If planned_subtopics are provided, supervisor will see them as recommended topics to prefer.
        
        This is the main research loop that:
        1. Asks an LLM supervisor to evaluate current findings
        2. Decides what topic to research next (preferring planned topics if provided)
        3. Researches the chosen topic
        4. Compresses notes periodically (when 4+ notes) to manage token usage
        5. Repeats until supervisor says "complete" or max iterations reached
        
        Returns:
            List of ResearchNote objects from all research iterations
        """
        notes = []
        compressed_context = ""
        researched_topics = set()
        iteration = 0
        
        while iteration < self.max_iterations:
            iteration += 1
            logger.info(f"Supervisor iteration {iteration}/{self.max_iterations}")
            
            await self._send_status(
                request_id,
                "researching",
                "Evaluating research",
                f"Assessing findings and deciding next steps (iteration {iteration})",
                {"iteration": iteration}
            )
            
            findings_summary = ""
            if compressed_context:
                findings_summary = f"\n\n## Current Research Findings (Compressed):\n\n{compressed_context}\n"
            elif notes:
                findings_summary = "\n\n## Current Research Findings:\n\n"
                for i, note in enumerate(notes, 1):
                    findings_summary += f"### Research {i}: {note.subtopic}\n"
                    findings_summary += f"{note.summary_markdown[:500]}...\n\n"
            
            researched_list = "\n".join([f"- {topic}" for topic in sorted(researched_topics)])
            
            planned_list = ""
            if planned_subtopics:
                remaining_planned = [
                    topic for topic in planned_subtopics
                    if not any(
                        topic.lower().strip() in researched.lower().strip() or
                        researched.lower().strip() in topic.lower().strip()
                        for researched in researched_topics
                    )
                ]
                if remaining_planned:
                    planned_list = f"\n\nPlanned Topics (prefer these):\n" + "\n".join([f"- {topic}" for topic in remaining_planned])
            
            supervisor_prompt = f"""You are evaluating research progress.

Research Brief: {brief}
{planned_list}

Researched Topics:
{researched_list if researched_topics else "None yet"}

{findings_summary}

Based on the research findings so far:
1. What do we know?
2. What's missing or needs deeper investigation?
3. Should we research a new topic, go deeper on an existing one, or is research complete?

Respond with JSON:
{{
    "action": "research_topic" | "research_complete",
    "topic": "specific topic to research (if action is research_topic)",
    "reason": "why you're making this decision"
}}

Guidelines:
- **PREFER topics from the "Planned Topics" list** - use the EXACT wording from planned topics when possible
- If research is comprehensive and covers all key aspects, use "research_complete"
- If there are important gaps, use "research_topic" with a specific, focused topic
- **CRITICAL: Topic Format for Search**
  - The topic you specify MUST be formatted as a ready-to-use search query for EXA
  - Include the main subject/entity from the research brief in EVERY topic
  - If the entity name is ambiguous, add disambiguating terms (e.g., "Tesla Inc." not "Tesla")
  - Make topics specific enough to avoid generic results (3-10 words)
- Don't repeat topics we've already researched
- Maximum {self.max_concurrent_research_units} topics can be researched in parallel"""

            response = await execute_llm_chat(
                llm=self.llm,
                system_prompt=lead_researcher_prompt(get_today_str(), self.max_concurrent_research_units),
                user_prompt=supervisor_prompt,
                parse_json=True,
                extract_json=True,
                conversation_history=conversation_history
            )
            
            fallback_response = {"action": "research_topic", "topic": brief, "reason": "Need to start research"}
            response = parse_json_response_with_fallback(response, fallback_response)
            
            action = response.get("action", "research_complete")
            
            if action == "research_complete":
                reason = response.get("reason", "Research is comprehensive")
                logger.info(f"Research complete: {reason}")
                await self._send_status(
                    request_id,
                    "researching",
                    "Research complete",
                    f"Supervisor determined research is comprehensive: {reason}",
                    {"iterations": iteration}
                )
                break
            
            topic = response.get("topic", "")
            if not topic:
                logger.warning("Supervisor requested research_topic but didn't provide topic, completing")
                break
            
            topic_lower = topic.lower().strip()
            if any(existing.lower().strip() in topic_lower or topic_lower in existing.lower().strip() 
                   for existing in researched_topics):
                if iteration >= self.max_iterations - 1:
                    logger.warning("Reached near max iterations with similar topics, completing research")
                    break
            
            researched_topics.add(topic)
            
            note = await self.subtopic_researcher.research(
                request_id=request_id,
                subtopic=topic,
                iteration=iteration - 1,
                original_query=original_query,
                research_brief=brief,
                conversation_history=conversation_history
            )
            notes.append(note)
            
            # Compress notes when we have 4+ to manage token limits
            # For 2-3 notes, compression is optional and may not be worth the LLM call
            if len(notes) >= 4:
                compressed_context = await compress_notes(
                    llm=self.llm,
                    request_id=request_id,
                    notes=notes,
                    status_callback=self.status_callback
                )
            
            await asyncio.sleep(0.5)
        
        if iteration >= self.max_iterations:
            logger.warning(f"Reached max iterations ({self.max_iterations}), completing research")
            await self._send_status(
                request_id,
                "researching",
                "Max iterations reached",
                f"Completed {iteration} research iterations",
                {"iterations": iteration}
            )
        
        logger.info(f"Completed {iteration} iterations → {len(notes)} research topics")
        return notes
    
    async def generate_final_report(
        self,
        request_id: str,
        title: str,
        brief: str,
        notes: List[ResearchNote]
    ) -> str:
        """
        Generate final research report
        
        Returns:
            Final report as markdown string
        """
        return await generate_report(
            llm=self.llm,
            request_id=request_id,
            title=title,
            brief=brief,
            notes=notes,
            status_callback=self.status_callback,
            report_callback=self.report_callback
        )
