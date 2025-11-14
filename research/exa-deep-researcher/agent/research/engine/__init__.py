"""
Research engine

This package handles:
- Subtopic research execution
- Source synthesis and analysis
"""

from .subtopic import ResearchSubtopic
from .synthesizer import synthesize_findings

__all__ = ["ResearchSubtopic", "synthesize_findings"]

