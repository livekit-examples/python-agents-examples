#!/usr/bin/env python3
"""
---
title: RAG Voice Agent
category: rag
tags: [annoy_index, vector_search, embeddings, livekit_docs, deduplication]
difficulty: advanced
description: RAG-enabled agent with vector search for LiveKit documentation
demonstrates:
  - Annoy vector index loading and querying
  - OpenAI embeddings for semantic search
  - Result deduplication with seen tracking
  - Function tool for document search
  - Paragraph-based context retrieval
  - Noise cancellation with BVC
---
"""

"""
RAG-enabled voice agent example for LiveKit Agents 1.0

This agent uses the RAG (Retrieval Augmented Generation) plugin to provide
information from a knowledge base when answering user questions.

Before running this agent:
1. Make sure you have your OpenAI API key in a .env file
2. Run build_rag_data.py to build the RAG database
"""

import logging
import pickle
from pathlib import Path
from typing import Literal, Any
from collections.abc import Iterable
from dataclasses import dataclass
from dotenv import load_dotenv
import annoy

from livekit.agents import (
    JobContext,
    WorkerOptions,
    cli,
    RunContext,
    function_tool,
    RoomInputOptions,
    Agent,
    AgentSession,
)
from livekit.plugins import openai, silero, deepgram, noise_cancellation
from livekit.plugins.turn_detector.english import EnglishModel

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("rag-agent")

# RAG Index Types and Classes
Metric = Literal["angular", "euclidean", "manhattan", "hamming", "dot"]
ANNOY_FILE = "index.annoy"
METADATA_FILE = "metadata.pkl"


@dataclass
class _FileData:
    f: int
    metric: Metric
    userdata: dict[int, Any]


@dataclass
class Item:
    i: int
    userdata: Any
    vector: list[float]


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

    def query(
        self, vector: list[float], n: int, search_k: int = -1
    ) -> list[QueryResult]:
        ids = self._index.get_nns_by_vector(
            vector, n, search_k=search_k, include_distances=True
        )
        return [
            QueryResult(userdata=self._filedata.userdata[i], distance=distance)
            for i, distance in zip(*ids)
        ]


class RAGEnrichedAgent(Agent):
    """
    An agent that can answer questions using RAG (Retrieval Augmented Generation).
    """

    def __init__(self) -> None:
        """Initialize the RAG-enabled agent."""
        super().__init__(
            instructions="""
                You are a helpful voice assistant specializing in knowledge about LiveKit ("live" pronounced as in "live stream").
                You can answer questions about LiveKit, the LiveKit Agents SDK, and more. 
                Your responses should always be concise and suitable for text-to-speech output, so be casual and avoid using markdown or other special formatting.
            """,
        )

        # Initialize RAG components
        vdb_dir = Path(__file__).parent / "data"
        data_path = vdb_dir / "paragraphs.pkl"

        if not vdb_dir.exists() or not data_path.exists():
            logger.warning(
                "RAG database not found. Please run build_rag_data.py first:\n"
                "$ python build_rag_data.py"
            )
            return

        # Load RAG index and data
        self._index_path = vdb_dir
        self._data_path = data_path
        self._embeddings_dimension = 1536
        self._embeddings_model = "text-embedding-3-small"
        self._seen_results = set()  # Track previously seen results

        try:
            self._annoy_index = AnnoyIndex.load(str(self._index_path))
            with open(self._data_path, "rb") as f:
                self._paragraphs_by_uuid = pickle.load(f)
            logger.info("RAG database loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load RAG database: {e}")

    @function_tool
    async def livekit_docs_search(self, context: RunContext, query: str):
        """Lookup information in the LiveKit docs database. Will not return results already returned in previous lookups."""
        try:
            # Generate embeddings for the query
            query_embedding = await openai.create_embeddings(
                input=[query],
                model=self._embeddings_model,
                dimensions=self._embeddings_dimension,
            )

            # Query the index for more results than we need to ensure we have enough new content
            all_results = self._annoy_index.query(
                query_embedding[0].embedding, n=5
            )  # Get more results initially

            # Filter out previously seen results
            new_results = [
                r for r in all_results if r.userdata not in self._seen_results
            ]

            # If we don't have enough new results, clear the seen results and start fresh
            if len(new_results) == 0:
                return "No new results found."
            else:
                new_results = new_results[:2]  # Take top 2 new results

            # Build context from multiple relevant paragraphs
            context_parts = []
            for result in new_results:
                # Add result to seen set
                self._seen_results.add(result.userdata)

                paragraph = self._paragraphs_by_uuid.get(result.userdata, "")
                if paragraph:
                    # Extract source URL if available in the paragraph
                    source = "Unknown source"
                    if "from [" in paragraph:
                        source = paragraph.split("from [")[1].split("]")[0]
                        paragraph = paragraph.split("]")[1].strip()

                    context_parts.append(f"Source: {source}\nContent: {paragraph}\n")

            if not context_parts:
                return

            # Combine all context parts with clear separation
            full_context = "\n\n".join(context_parts)
            logger.info(
                f"Results for query: {query}, full context: {full_context.replace('\n', '\\n')}"
            )

            return full_context
        except Exception as e:
            return "Could not find any relevant information for that query."

    async def on_enter(self):
        """Called when the agent enters the session."""
        self.session.generate_reply(
            instructions="Briefly greet the user and offer your assistance with LiveKit."
        )


async def entrypoint(ctx: JobContext):
    """Main entrypoint for the agent."""
    session = AgentSession(
        stt=deepgram.STT(),
        llm=openai.LLM(model="gpt-4o"),
        tts=openai.TTS(
            instructions="You are a helpful assistant with a pleasant voice.",
            voice="ash",
        ),
        turn_detection=EnglishModel(),
        vad=silero.VAD.load(),
    )

    await session.start(
        agent=RAGEnrichedAgent(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
