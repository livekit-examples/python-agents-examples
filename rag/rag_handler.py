"""
---
title: RAG Handler Utility
category: rag
tags: [thinking_styles, rag_enrichment, agent_registration, context_injection]
difficulty: advanced
description: Reusable RAG handler with thinking styles and agent integration
demonstrates:
  - Three thinking styles (none, message, llm)
  - RAG context retrieval and enrichment
  - Agent method injection pattern
  - Function tool registration
  - Flexible thinking phase handling
  - Random message selection
---
"""

import logging
import pickle
import random
from enum import Enum
from pathlib import Path
from typing import List, Optional, Union, Any, Literal
from collections.abc import Iterable
from dataclasses import dataclass

import annoy

from livekit.agents.voice import Agent, RunContext
from livekit.agents.llm import function_tool
from livekit.plugins import openai

logger = logging.getLogger("rag-handler")

# RAG Index Types and Classes
Metric = Literal["angular", "euclidean", "manhattan", "hamming", "dot"]
ANNOY_FILE = "index.annoy"
METADATA_FILE = "metadata.pkl"

@dataclass
class Item:
    i: int
    userdata: Any
    vector: list[float]

@dataclass
class _FileData:
    f: int
    metric: Metric
    userdata: dict[int, Any]

@dataclass
class QueryResult:
    userdata: Any
    distance: float

class AnnoyIndex:
    def __init__(self, index: annoy.AnnoyIndex, filedata: _FileData) -> None:
        self._index = index
        self._filedata = filedata

    @classmethod
    def load(cls, path: str) -> "AnnoyIndex":
        p = Path(path)
        index_path = p / ANNOY_FILE
        metadata_path = p / METADATA_FILE

        with open(metadata_path, "rb") as f:
            metadata: _FileData = pickle.load(f)

        index = annoy.AnnoyIndex(metadata.f, metadata.metric)
        index.load(str(index_path))
        return cls(index, metadata)

    @property
    def size(self) -> int:
        return self._index.get_n_items()

    def items(self) -> Iterable[Item]:
        for i in range(self._index.get_n_items()):
            item = Item(
                i=i,
                userdata=self._filedata.userdata[i],
                vector=self._index.get_item_vector(i),
            )
            yield item

    def query(self, vector: list[float], n: int, search_k: int = -1) -> list[QueryResult]:
        ids = self._index.get_nns_by_vector(vector, n, search_k=search_k, include_distances=True)
        return [
            QueryResult(userdata=self._filedata.userdata[i], distance=distance)
            for i, distance in zip(*ids)
        ]

class ThinkingStyle(Enum):
    NONE = "none"
    MESSAGE = "message"
    LLM = "llm"

DEFAULT_THINKING_MESSAGES = [
    "Let me look that up...",
    "One moment while I check...",
    "I'll find that information for you...",
    "Just a second while I search...",
    "Looking into that now..."
]

DEFAULT_THINKING_PROMPT = "Generate a very short message to indicate that we're looking up the answer in the docs"

class RAGHandler:
    """
    Handler for Retrieval-Augmented Generation (RAG) in LiveKit agents 1.0.
    Provides flexible ways to handle delays during RAG lookups.
    
    Example usage:
        # In your agent class
        def __init__(self) -> None:
            super().__init__(...)
            
            # Initialize RAG handler
            self.rag_handler = RAGHandler(
                index_path="data",
                data_path="my_data.pkl",
                thinking_style="message"
            )
    """
    
    def __init__(
        self,
        index_path: Union[str, Path],
        data_path: Union[str, Path],
        thinking_style: Union[str, ThinkingStyle] = ThinkingStyle.MESSAGE,
        thinking_messages: Optional[List[str]] = None,
        thinking_prompt: Optional[str] = None,
        embeddings_dimension: int = 1536,
        embeddings_model: str = "text-embedding-3-small"
    ):
        """
        Initialize the RAG handler.
        
        Args:
            index_path: Path to the Annoy index file
            data_path: Path to the pickled data file containing paragraphs
            thinking_style: How to handle delays during RAG lookups
            thinking_messages: Custom messages to use with MESSAGE style
            thinking_prompt: Custom prompt to use with LLM style
            embeddings_dimension: Dimension of embeddings to use
            embeddings_model: OpenAI model to use for embeddings
        """
        self._index_path = Path(index_path)
        self._data_path = Path(data_path)
        self._thinking_style = thinking_style if isinstance(thinking_style, ThinkingStyle) else ThinkingStyle(thinking_style)
        self._thinking_messages = thinking_messages or DEFAULT_THINKING_MESSAGES
        self._thinking_prompt = thinking_prompt or DEFAULT_THINKING_PROMPT
        self._embeddings_dimension = embeddings_dimension
        self._embeddings_model = embeddings_model
        
        # Load index and data
        if not self._index_path.exists():
            raise FileNotFoundError(f"Annoy index not found at {self._index_path}")
        if not self._data_path.exists():
            raise FileNotFoundError(f"Data file not found at {self._data_path}")
            
        self._annoy_index = AnnoyIndex.load(str(self._index_path))
        with open(self._data_path, "rb") as f:
            self._paragraphs_by_uuid = pickle.load(f)
    
    async def _handle_thinking(self, agent: Agent) -> None:
        """Handle the thinking phase based on the configured style."""
        if self._thinking_style == ThinkingStyle.NONE:
            return
            
        elif self._thinking_style == ThinkingStyle.MESSAGE:
            await agent.session.say(random.choice(self._thinking_messages))
            
        elif self._thinking_style == ThinkingStyle.LLM:
            # Create a thinking message using the LLM
            response = await agent._llm.complete(self._thinking_prompt)
            await agent.session.say(response.text)
    
    async def retrieve_context(self, query: str) -> str:
        """
        Retrieve relevant context from the RAG database
        
        Args:
            query: The query to search for relevant context
            
        Returns:
            The retrieved context, or an empty string if no relevant context was found
        """
        # Generate embeddings for the query
        query_embedding = await openai.create_embeddings(
            input=[query],
            model=self._embeddings_model,
            dimensions=self._embeddings_dimension
        )
        
        # Query the index
        results = self._annoy_index.query(query_embedding[0].embedding, n=1)
        
        if not results:
            return ""
            
        # Get the most relevant paragraph
        paragraph = self._paragraphs_by_uuid.get(results[0].userdata, "")
        return paragraph
    
    async def enrich_with_rag(self, agent: Agent, context: RunContext, query: str) -> None:
        """
        Enrich the agent's response with RAG
        
        Args:
            agent: The agent to enrich
            context: The RunContext from the function call
            query: The query to search for
        """
        # Handle thinking phase
        await self._handle_thinking(agent)
        
        # Retrieve relevant context
        relevant_context = await self.retrieve_context(query)
        
        if not relevant_context:
            await agent.session.say("I couldn't find any relevant information about that.")
            return
        
        # Generate response with context
        context_prompt = f"""
        Question: {query}
        
        Relevant information:
        {relevant_context}
        
        Using the relevant information above, please provide a helpful response to the question.
        Keep your response concise and directly answer the question.
        """
        
        response = await agent._llm.complete(context_prompt)
        await agent.session.say(response.text)

    def register_with_agent(self, agent: Agent) -> None:
        """
        Register the RAG handler with an agent
        
        Args:
            agent: The agent to register with
        """
        # Inject the function tool into the agent
        @function_tool
        async def lookup_info(self, context: RunContext, query: str):
            """
            Use this function to look up information using RAG when the user asks a question
            about a topic that might be in our knowledge base.
            
            Args:
                query: The question or topic to look up
            """
            logger.info(f"Looking up information for: {query}")
            await self.rag_handler.enrich_with_rag(self, context, query)
        
        # Add the function and rag_handler to the agent
        agent.lookup_info = lookup_info.__get__(agent)
        agent.rag_handler = self 