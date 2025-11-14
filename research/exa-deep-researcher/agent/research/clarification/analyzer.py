"""
Autonomous clarification analysis

This module uses an LLM to analyze search results and determine
if clarification is needed before starting deep research.
"""
import logging
from typing import List, Optional, Tuple

from agent.schemas import EXAResult
from agent.utils import execute_llm_chat

logger = logging.getLogger("clarification-analyzer")


class AutonomousClarification:
    """
    Analyzes search results to determine if user clarification is needed
    
    This class uses an LLM to evaluate whether search results match the user's
    intent. If the query is ambiguous or results are unclear, it requests
    clarification before proceeding with expensive deep research.
    """
    
    def __init__(self, llm):
        """
        Initialize clarification analyzer
        
        Args:
            llm: LLM instance for analysis
        """
        self.llm = llm
    
    async def analyze(
        self,
        query: str,
        results: List[EXAResult],
        conversation_history: Optional[list] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Autonomously determine if clarification is needed based on search results
        
        After doing an initial search, this function uses an LLM to analyze whether the
        results match what the user is looking for. If the query is ambiguous or results
        are unclear, it asks for clarification before proceeding with deep research.
        
        This prevents wasting time researching the wrong thing.
        
        Args:
            query: User's search query
            results: List of search results to analyze
            conversation_history: Optional conversation context
            
        Returns:
            Tuple of (needs_clarification: bool, clarification_message: Optional[str])
            - If needs_clarification is False, proceed with research
            - If True, clarification_message contains what to ask the user
        """
        if not results:
            return True, f"I couldn't find any results for '{query}'. Could you clarify what you're looking for?"
        
        results_summary = "\n".join([
            f"{i+1}. {r.title} - {r.url[:60]}..."
            for i, r in enumerate(results[:5])  # Show top 5 results
        ])
        
        clarification_prompt = f"""Analyze whether these search results match what the user is looking for.

User Query: {query}

Search Results Found:
{results_summary}

Based on the query and results:
1. Do these results clearly match what the user is asking for?
2. Is the query specific enough that we can proceed with research?
3. Are there any ambiguities that need clarification?

Respond with JSON:
{{
    "needs_clarification": true/false,
    "confidence": "high/medium/low",
    "reason": "brief explanation",
    "clarification_message": "what to ask user if needed, or null"
}}

If confidence is "high" and results clearly match, set needs_clarification to false.
If query is ambiguous or results are unclear, set needs_clarification to true."""
        
        try:
            response = await execute_llm_chat(
                llm=self.llm,
                system_prompt="You are an expert at determining if search results match user intent. Be decisive - only ask for clarification if truly needed.",
                user_prompt=clarification_prompt,
                parse_json=True,
                extract_json=True,
                conversation_history=conversation_history
            )
            
            if isinstance(response, dict):
                needs_clarification = response.get("needs_clarification", False)
                clarification_message = response.get("clarification_message")
                confidence = response.get("confidence", "medium")
                
                logger.info(f"Clarification analysis: needs={needs_clarification}, confidence={confidence}")
                
                if needs_clarification and clarification_message:
                    return True, clarification_message
                elif needs_clarification:
                    return True, f"I found some results for '{query}', but I want to make sure I'm researching the right thing. Could you clarify?"
                else:
                    return False, None
            else:
                logger.warning(f"Clarification analysis returned non-dict: {type(response)}")
                return True, f"I found some results for '{query}'. Is this what you're looking for?"
                
        except Exception as e:
            logger.error(f"Error in autonomous clarification: {e}")
            return True, f"I found some results for '{query}'. Could you confirm this is what you're looking for?"

