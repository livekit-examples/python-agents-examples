"""
Event handlers for agent

This package contains:
- RPC communication with UI
- Status, notes, and report update handling
"""

from .rpc import send_rpc_to_ui_safe, format_status_payload, format_notes_payload, format_report_payload
from .status import StatusHandler

__all__ = [
    "send_rpc_to_ui_safe",
    "format_status_payload",
    "format_notes_payload",
    "format_report_payload",
    "StatusHandler",
]

