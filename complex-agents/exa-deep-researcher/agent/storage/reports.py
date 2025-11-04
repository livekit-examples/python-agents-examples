"""
Report storage to disk

This module handles saving research reports to the local filesystem
with proper naming and formatting.
"""
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("report-storage")


def generate_filename(title: str) -> str:
    """
    Generate a safe filename for a report
    
    Creates a timestamp-prefixed filename with sanitized title.
    
    Args:
        title: Report title
        
    Returns:
        Safe filename string (e.g., "2025-01-15_123456_Research_Topic.md")
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_title = safe_title[:50]  # Limit length
    return f"{timestamp}_{safe_title}.md"


async def save_report(title: str, report: str, base_dir: Path = None) -> Path:
    """
    Save research report to disk
    
    Creates a reports directory if it doesn't exist and saves the report
    as a markdown file with metadata.
    
    Args:
        title: Report title
        report: Full report content
        base_dir: Base directory for reports (defaults to script directory)
        
    Returns:
        Path to saved report file
        
    Raises:
        Exception: If report cannot be saved
    """
    try:
        if base_dir is None:
            base_dir = Path(__file__).parent.parent.parent
        
        reports_dir = base_dir / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        filename = generate_filename(title)
        filepath = reports_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n")
            f.write(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            f.write("---\n\n")
            f.write(report)
        
        logger.info(f"Report saved to: {filepath}")
        return filepath
        
    except Exception as e:
        logger.error(f"Error saving report: {e}")
        raise

