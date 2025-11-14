"""
Storage management for research artifacts

This package handles:
- Saving reports to disk
- File naming and organization
"""

from .reports import save_report, generate_filename

__all__ = ["save_report", "generate_filename"]

