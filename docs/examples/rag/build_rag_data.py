#!/usr/bin/env python3
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv
from rag_db_builder import RAGBuilder

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("build-rag-data")

# Load environment variables
load_dotenv()


async def main() -> None:
    """
    Build the RAG database from the scraped docs content.

    Usage:
        1. Run scrape_docs.py to scrape the docs content
        2. Run this script to build the RAG database
        3. The database will be created in the 'data' directory
    """
    # Check if raw_data.txt exists
    raw_data_path = Path(__file__).parent / "data/raw_data.txt"
    if not raw_data_path.exists():
        logger.error(
            "raw_data.txt not found. Please run scrape_docs.py first:\n"
            "$ python scrape_docs.py"
        )
        return

    # Create and build the RAG database
    output_dir = Path(__file__).parent / "data"
    output_dir.mkdir(exist_ok=True)

    logger.info("Building RAG database...")
    await RAGBuilder.create_from_file(
        file_path=raw_data_path,
        index_path=output_dir,
        data_path=output_dir / "paragraphs.pkl",
        embeddings_dimension=1536,
    )
    logger.info("RAG database successfully built!")
    logger.info(f"Index saved to: {output_dir}")
    logger.info(f"Data saved to: {output_dir / 'paragraphs.pkl'}")


if __name__ == "__main__":
    asyncio.run(main())
