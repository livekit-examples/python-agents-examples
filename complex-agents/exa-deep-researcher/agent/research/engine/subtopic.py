"""
Subtopic research execution

This module handles researching a single subtopic, including
searching EXA, fetching content, and synthesizing findings.
"""
import logging
from typing import Optional, Callable
from datetime import datetime

from agent.schemas import EXASearchParams, EXAContentOptions, ResearchNote
from agent.exa_client import EXAClient
from agent.utils import fetch_contents_in_batches, execute_llm_chat
from agent.prompts import generate_search_query_prompt
from .synthesizer import synthesize_findings

logger = logging.getLogger("subtopic-research")


class ResearchSubtopic:
    """
    Handles researching a single subtopic using EXA
    
    This class coordinates the research workflow for one subtopic:
    1. Search EXA for relevant sources
    2. Fetch content from those sources
    3. Synthesize findings into a note
    """
    
    def __init__(
        self,
        exa_client: EXAClient,
        llm,
        max_results_per_search: int = 10,
        max_concurrent_fetches: int = 3,
        status_callback: Optional[Callable] = None,
        notes_callback: Optional[Callable] = None
    ):
        """
        Initialize subtopic researcher
        
        Args:
            exa_client: EXA API client
            llm: LLM instance for synthesis
            max_results_per_search: Maximum results per search
            max_concurrent_fetches: Max parallel content fetches
            status_callback: Optional callback for status updates
            notes_callback: Optional callback for completed notes
        """
        self.exa_client = exa_client
        self.llm = llm
        self.max_results_per_search = max_results_per_search
        self.max_concurrent_fetches = max_concurrent_fetches
        self.status_callback = status_callback
        self.notes_callback = notes_callback
    
    async def research(
        self,
        request_id: str,
        subtopic: str,
        iteration: int,
        original_query: str = "",
        research_brief: str = "",
        conversation_history: Optional[list] = None
    ) -> ResearchNote:
        """
        Research a single subtopic using EXA
        
        This is the core research function that:
        1. Searches EXA for relevant sources about the subtopic
        2. Fetches the actual content from those sources
        3. Uses an LLM to synthesize findings from the sources
        4. Extracts citations and returns a ResearchNote
        
        Args:
            request_id: Request identifier
            subtopic: The specific subtopic to research
            iteration: Iteration index
            original_query: The original user query/goal
            research_brief: The full research brief with context
            conversation_history: Optional conversation context
            
        Returns:
            ResearchNote with findings and citations
        """
        if self.status_callback:
            logger.info(f"[RESEARCHING] Starting research for: {subtopic} (requestId={request_id})")
            await self.status_callback(
                request_id,
                "researching",
                "Starting research",
                f"Investigating: {subtopic}",
                {"subtopic": subtopic}
            )
        
        # Generate contextualized search queries using LLM
        query_prompt = generate_search_query_prompt(subtopic, original_query, research_brief)
        queries_response = await execute_llm_chat(
            llm=self.llm,
            system_prompt="You are a search query generator. Return only valid JSON.",
            user_prompt=query_prompt,
            parse_json=True,
            extract_json=True,
            conversation_history=conversation_history
        )
        
        search_queries = []
        if isinstance(queries_response, list):
            search_queries = [str(q) for q in queries_response[:3]]
        elif isinstance(queries_response, dict) and "queries" in queries_response:
            search_queries = queries_response["queries"][:3]
        
        if not search_queries:
            logger.warning(f"Failed to generate search queries, using subtopic: {subtopic}")
            search_queries = [subtopic]
        
        logger.info(f"Generated search queries: {search_queries}")
        
        primary_query = search_queries[0] if search_queries else subtopic
        search_params = EXASearchParams(
            query=primary_query,
            num_results=self.max_results_per_search,
            use_autoprompt=None
        )
        
        results = await self.exa_client.search(search_params)
        
        logger.info(f"Found {len(results)} results for subtopic: {subtopic}")
        
        if not results:
            return ResearchNote(
                subtopic=subtopic,
                summary_markdown=f"No results found for: {subtopic}",
                citations=[],
                timestamp=datetime.now()
            )
        
        if self.status_callback:
            await self.status_callback(
                request_id,
                "researching",
                "Gathering sources",
                f"Found {len(results)} relevant sources about {subtopic}",
                {"subtopic": subtopic, "results": len(results)}
            )
        
        content_options = EXAContentOptions(
            text=True,
            max_characters=5000,
            livecrawl="fallback"
        )
        
        result_urls = [r.url for r in results]
        all_contents = await fetch_contents_in_batches(
            self.exa_client, result_urls, content_options, self.max_concurrent_fetches
        )
        
        if self.status_callback:
            await self.status_callback(
                request_id,
                "researching",
                "Synthesizing findings",
                f"Analyzing {len(all_contents)} sources about {subtopic}",
                {"subtopic": subtopic, "sources_fetched": len(all_contents)}
            )
        
        note = await synthesize_findings(
            llm=self.llm,
            subtopic=subtopic,
            sources=all_contents,
            original_query=original_query,
            research_brief=research_brief,
            conversation_history=conversation_history
        )
        
        if self.notes_callback:
            await self.notes_callback(request_id, note)
        
        return note

