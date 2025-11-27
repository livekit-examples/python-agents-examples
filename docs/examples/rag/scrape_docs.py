#!/usr/bin/env python3
import asyncio
import logging
import re
from pathlib import Path
from typing import List, Set
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("docs-scraper")

# Load environment variables
load_dotenv()

BASE_URL = "https://docs.livekit.io"
SITEMAP_URL = f"{BASE_URL}/sitemap.xml"
OUTPUT_FILE = Path(__file__).parent / "data/raw_data.txt"
EXCLUDED_PATHS = ["/reference"]  # Paths to exclude from scraping

class DocsScraper:
    def __init__(self):
        self.visited_urls: Set[str] = set()
        self.content: List[str] = []
        self.session = None

    async def init_session(self):
        """Initialize the aiohttp session."""
        self.session = aiohttp.ClientSession()

    async def close_session(self):
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()

    def should_exclude_url(self, url: str) -> bool:
        """Check if a URL should be excluded from scraping."""
        parsed = urlparse(url)
        return any(parsed.path.startswith(path) for path in EXCLUDED_PATHS)

    async def fetch_sitemap(self) -> List[str]:
        """Fetch and parse the sitemap to get all URLs."""
        async with self.session.get(SITEMAP_URL) as response:
            if response.status != 200:
                raise Exception(f"Failed to fetch sitemap: {response.status}")
            
            content = await response.text()
            soup = BeautifulSoup(content, "xml")
            urls = [loc.text for loc in soup.find_all("loc")]
            
            # Filter out excluded URLs and ensure they're from docs.livekit.io
            return [
                url for url in urls 
                if url.startswith(BASE_URL) and not self.should_exclude_url(url)
            ]

    async def fetch_page(self, url: str) -> str:
        """Fetch a single page and extract its content."""
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch {url}: {response.status}")
                    return ""
                
                content = await response.text()
                soup = BeautifulSoup(content, "html.parser")
                
                # Extract the main content
                main_content = soup.find("main")
                if not main_content:
                    return ""
                
                # Remove unwanted elements
                for element in main_content.find_all(["nav", "footer", "header", "script", "style"]):
                    element.decompose()
                
                # Clean up the text
                text = main_content.get_text(separator="\n", strip=True)
                text = re.sub(r"\n\s*\n", "\n\n", text)  # Remove excessive newlines
                return text.strip()
                
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return ""

    async def scrape(self):
        """Main scraping function."""
        await self.init_session()
        try:
            # Get all URLs from sitemap
            urls = await self.fetch_sitemap()
            logger.info(f"Found {len(urls)} URLs to scrape")
            
            # Process each URL
            for url in urls:
                if url in self.visited_urls:
                    continue
                    
                self.visited_urls.add(url)
                logger.info(f"Scraping {url}")
                
                content = await self.fetch_page(url)
                if content:
                    self.content.append(f"Content from {url}:\n\n{content}\n\n")
                    
        finally:
            await self.close_session()

    def save_content(self):
        """Save the scraped content to a file."""
        with open(OUTPUT_FILE, "w") as f:
            f.write("\n".join(self.content))
        logger.info(f"Saved content to {OUTPUT_FILE}")

async def main():
    """Main function to run the scraper."""
    scraper = DocsScraper()
    await scraper.scrape()
    scraper.save_content()

if __name__ == "__main__":
    asyncio.run(main()) 