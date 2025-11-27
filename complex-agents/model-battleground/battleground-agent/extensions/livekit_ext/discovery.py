from importlib.metadata import entry_points

from .log import log
from .registry import _REGISTRY  # type: ignore[attr-defined]


def discover(group: str = "livekit_agents.extensions") -> None:
    """Load entry points into the registry."""

    try:
        entries = entry_points(group=group)
    except Exception:
        log.exception("extension entry point discovery failed", extra={"group": group})
        return

    for entry in entries:
        try:
            _REGISTRY[entry.name] = entry.load()
        except Exception:
            log.exception("failed to load extension entry point", extra={"entry": entry.name})
