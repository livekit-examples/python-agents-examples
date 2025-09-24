"""
---
title: RAG Database Builder
category: rag
tags: [annoy_index, sentence_chunking, embeddings_generation, vector_database]
difficulty: advanced
description: Builds vector databases for RAG from text documents
demonstrates:
  - Annoy index construction and saving
  - Text chunking with SentenceChunker
  - OpenAI embeddings generation
  - Progress tracking with tqdm
  - Content cleaning and filtering
  - UUID-based paragraph storage
  - Factory pattern for builder creation
---
"""

import pickle
import uuid
import logging
from pathlib import Path
from typing import List, Optional, Union, Literal, Callable, Any
from collections.abc import Iterable
from dataclasses import dataclass
import aiohttp
from tqdm import tqdm
import annoy

from livekit.agents import tokenize
from livekit.plugins import openai

logger = logging.getLogger("rag-builder")

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


class IndexBuilder:
    def __init__(self, f: int, metric: Metric) -> None:
        self._index = annoy.AnnoyIndex(f, metric)
        self._filedata = _FileData(f=f, metric=metric, userdata={})
        self._i = 0

    def save(self, path: str) -> None:
        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)
        index_path = p / ANNOY_FILE
        metadata_path = p / METADATA_FILE
        self._index.save(str(index_path))
        with open(metadata_path, "wb") as f:
            pickle.dump(self._filedata, f)

    def build(self, trees: int = 50, jobs: int = -1) -> AnnoyIndex:
        # n_jobs=-1 means use all available cores
        self._index.build(n_trees=trees, n_jobs=jobs)
        return AnnoyIndex(self._index, self._filedata)

    def add_item(self, vector: list[float], userdata: Any) -> None:
        self._index.add_item(self._i, vector)
        self._filedata.userdata[self._i] = userdata
        self._i += 1


class SentenceChunker:
    def __init__(
        self,
        *,
        max_chunk_size: int = 120,
        chunk_overlap: int = 30,
        paragraph_tokenizer: Callable[
            [str], list[str]
        ] = tokenize.basic.tokenize_paragraphs,
        sentence_tokenizer: tokenize.SentenceTokenizer = tokenize.basic.SentenceTokenizer(),  # noqa: B008
        word_tokenizer: tokenize.WordTokenizer = tokenize.basic.WordTokenizer(  # noqa: B008
            ignore_punctuation=False
        ),
    ) -> None:
        self._max_chunk_size = max_chunk_size
        self._chunk_overlap = chunk_overlap
        self._paragraph_tokenizer = paragraph_tokenizer
        self._sentence_tokenizer = sentence_tokenizer
        self._word_tokenizer = word_tokenizer

    def chunk(self, *, text: str) -> list[str]:
        chunks = []

        buf_words: list[str] = []
        for paragraph in self._paragraph_tokenizer(text):
            last_buf_words: list[str] = []

            for sentence in self._sentence_tokenizer.tokenize(text=paragraph):
                for word in self._word_tokenizer.tokenize(text=sentence):
                    reconstructed = self._word_tokenizer.format_words(
                        buf_words + [word]
                    )

                    if len(reconstructed) > self._max_chunk_size:
                        while (
                            len(self._word_tokenizer.format_words(last_buf_words))
                            > self._chunk_overlap
                        ):
                            last_buf_words = last_buf_words[1:]

                        new_chunk = self._word_tokenizer.format_words(
                            last_buf_words + buf_words
                        )
                        chunks.append(new_chunk)
                        last_buf_words = buf_words
                        buf_words = []

                    buf_words.append(word)

            if buf_words:
                while (
                    len(self._word_tokenizer.format_words(last_buf_words))
                    > self._chunk_overlap
                ):
                    last_buf_words = last_buf_words[1:]

                new_chunk = self._word_tokenizer.format_words(
                    last_buf_words + buf_words
                )
                chunks.append(new_chunk)
                buf_words = []

        return chunks


class RAGBuilder:
    """
    Builder for creating and managing RAG (Retrieval-Augmented Generation) databases.
    Handles data preparation, embedding generation, and vector database creation.

    Example usage:
        builder = RAGBuilder(
            index_path="data",
            data_path="my_data.pkl",
            embeddings_dimension=1536
        )

        # Build from raw text file
        await builder.build_from_file("raw_data.txt")

        # Or build from list of texts
        await builder.build_from_texts([
            "First paragraph of content",
            "Second paragraph of content",
            ...
        ])
    """

    def __init__(
        self,
        index_path: Union[str, Path],
        data_path: Union[str, Path],
        embeddings_dimension: int = 1536,
        embeddings_model: str = "text-embedding-3-small",
        metric: str = "angular",
    ):
        """
        Initialize the RAG builder.

        Args:
            index_path: Path where the Annoy index will be saved
            data_path: Path where the paragraph data will be saved
            embeddings_dimension: Dimension of embeddings to use
            embeddings_model: OpenAI model to use for embeddings
            metric: Distance metric for Annoy index ("angular", "euclidean", or "manhattan")
        """
        self._index_path = Path(index_path)
        self._data_path = Path(data_path)
        self._embeddings_dimension = embeddings_dimension
        self._embeddings_model = embeddings_model
        self._metric = metric

    def _clean_content(self, text: str) -> str:
        """
        Clean the content by removing navigation elements and UI components.
        """
        # Remove common navigation elements
        lines = text.split('\n')
        cleaned_lines = []
        
        # Skip lines that are just navigation or UI elements
        skip_patterns = [
            'Docs', 'Search', 'GitHub', 'Slack', 'Sign in',
            'Home', 'AI Agents', 'Telephony', 'Recipes', 'Reference',
            'On this page', 'Get started with LiveKit today',
            'Content from https://docs.livekit.io/'
        ]
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Skip if line matches any skip patterns
            if any(pattern in line for pattern in skip_patterns):
                continue
                
            # Skip if line is just a URL or navigation link
            if line.startswith('http') or line.startswith('[') or line.endswith(']'):
                continue
                
            cleaned_lines.append(line)
            
        return '\n'.join(cleaned_lines)

    async def _create_embeddings(
        self, text: str, http_session: Optional[aiohttp.ClientSession] = None
    ) -> openai.EmbeddingData:
        """Create embeddings for a single text."""
        results = await openai.create_embeddings(
            input=[text],
            model=self._embeddings_model,
            dimensions=self._embeddings_dimension,
            http_session=http_session,
        )
        return results[0]

    async def build_from_texts(
        self, texts: List[str], show_progress: bool = True
    ) -> None:
        """
        Build the RAG database from a list of texts.
        Each text will be treated as a separate paragraph/document.

        Args:
            texts: List of text strings to process
            show_progress: Whether to show a progress bar
        """
        # Create parent directories if they don't exist
        self._index_path.parent.mkdir(parents=True, exist_ok=True)
        self._data_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiohttp.ClientSession() as http_session:
            idx_builder = IndexBuilder(
                f=self._embeddings_dimension, metric=self._metric
            )

            # Clean and filter texts
            cleaned_texts = []
            for text in texts:
                cleaned = self._clean_content(text)
                if cleaned:  # Only include non-empty cleaned texts
                    cleaned_texts.append(cleaned)

            # Generate UUIDs for each paragraph
            paragraphs_by_uuid = {str(uuid.uuid4()): text for text in cleaned_texts}

            # Create iterator with optional progress bar
            items = paragraphs_by_uuid.items()
            if show_progress:
                items = tqdm(items, desc="Creating embeddings")

            # Generate embeddings and add to index
            for p_uuid, paragraph in items:
                resp = await self._create_embeddings(paragraph, http_session)
                idx_builder.add_item(resp.embedding, p_uuid)

            # Build and save the index
            logger.info(f"Building index at {self._index_path}")
            idx_builder.build()
            idx_builder.save(str(self._index_path))

            # Save paragraph data
            logger.info(f"Saving paragraph data to {self._data_path}")
            with open(self._data_path, "wb") as f:
                pickle.dump(paragraphs_by_uuid, f)

    async def build_from_file(
        self, file_path: Union[str, Path], show_progress: bool = True
    ) -> None:
        """
        Build the RAG database from a text file.
        The file will be split into paragraphs using basic tokenization.

        Args:
            file_path: Path to the text file to process
            show_progress: Whether to show a progress bar
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Input file not found: {file_path}")

        # Read and tokenize the file
        with open(file_path, "r") as f:
            raw_data = f.read()

        paragraphs = tokenize.basic.tokenize_paragraphs(raw_data)
        await self.build_from_texts(paragraphs, show_progress)

    @classmethod
    async def create_from_file(
        cls,
        file_path: Union[str, Path],
        index_path: Union[str, Path],
        data_path: Union[str, Path],
        **kwargs,
    ) -> "RAGBuilder":
        """
        Convenience method to create and build a RAG database in one step.

        Args:
            file_path: Path to the input text file
            index_path: Path where the Annoy index will be saved
            data_path: Path where the paragraph data will be saved
            **kwargs: Additional arguments to pass to RAGBuilder constructor

        Returns:
            The constructed RAGBuilder instance
        """
        builder = cls(index_path, data_path, **kwargs)
        await builder.build_from_file(file_path)
        return builder
