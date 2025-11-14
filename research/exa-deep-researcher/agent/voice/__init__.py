"""
Voice update management

This package handles:
- Status queue for voice updates
- Voice synthesis of reports and status
"""

from .queue import StatusQueue
from .speaker import speak_final_report, truncate_for_speech

__all__ = ["StatusQueue", "speak_final_report", "truncate_for_speech"]

