"""
Quick search for clarification

This module performs quick searches to gather initial results
that help determine if clarification is needed.
"""
import logging
from typing import List, Callable, Optional

from agent.schemas import EXASearchParams, EXAResult
from agent.exa_client import EXAClient

logger = logging.getLogger("clarification-search")


async def quick_search(
    exa_client: EXAClient,
    request_id: str,
    query: str,
    num_results: int = 5,
    status_callback: Optional[Callable] = None
) -> List[EXAResult]:
    """
    Perform a quick naive search to get initial results for clarification
    
    This search is fast and limited in scope - just enough to understand
    if the query is clear and results are relevant.
    
    Args:
        exa_client: EXA API client
        request_id: Request identifier
        query: Search query
        num_results: Number of results to fetch (default: 5)
        status_callback: Optional callback for status updates
        
    Returns:
        List of EXA search results (typically 3-5 results)
    """
    if status_callback:
        logger.info(f"🔍 [CLARIFYING] Quick search starting for: {query} (requestId={request_id})")
        await status_callback(
            request_id,
            "clarifying",
            "Quick search",
            f"Searching for: {query}",
            {}
        )
    
    search_params = EXASearchParams(
        query=query,
        num_results=num_results,
        use_autoprompt=None
    )
    
    results = await exa_client.search(search_params)
    
    logger.info(f"Quick search found {len(results)} results for: {query}")
    
    return results

