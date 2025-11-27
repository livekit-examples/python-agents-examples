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

# RAG-Enriched Voice Agent

This sample project demonstrates a Retrieval-Augmented Generation (RAG) enabled voice agent using LiveKit Agents 1.0. The example scrapes the LiveKit docs site, builds a local index, and then provides that data on demand to the assistant via a function tool.

## Prerequisites

- Python 3.9 or higher
- OpenAI API key
- Deepgram API key
- LiveKit server

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the project root with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key
   DEEPGRAM_API_KEY=your_deepgram_api_key
   LIVEKIT_URL=your_livekit_url
   LIVEKIT_API_KEY=your_livekit_api_key
   LIVEKIT_API_SECRET=your_livekit_api_secret
   ```

## Project Structure

- `main.py`: Main agent implementation
- `scrape_docs.py`: Scraper for the LiveKit docs site
- `build_rag_data.py`: Script to build the RAG database from scraped docs
- `rag_db_builder.py`: Database builder implementation
- `rag_handler.py`: RAG processing logic
- `data/`: Directory for vector database files

## Usage

1. Scrape the docs site:
   ```bash
   python scrape_docs.py
   ```

2. Build the RAG database:
   ```bash
   python build_rag_data.py
   ```

3. Download model files:
   ```bash
   python main.py download-files
   ```

4. Run the agent:
   ```bash
   python main.py console
   ```

The agent will start and be ready to handle voice interactions. It will use the RAG system to provide contextually relevant answers to user questions.
