from typing import Any, Optional


def extract_text(chunk: Any) -> Optional[str]:
    """Best-effort extraction of text content from a streaming chunk."""

    delta = getattr(chunk, "delta", None)
    if delta is not None:
        content = getattr(delta, "content", None)
        if isinstance(content, str):
            return content

    if isinstance(chunk, str):
        return chunk

    return None


def inject_text(chunk: Any, new: str) -> Any:
    """Inject ``new`` content into ``chunk`` while keeping the original shape."""

    delta = getattr(chunk, "delta", None)
    if delta is not None and hasattr(delta, "content"):
        setattr(delta, "content", new)
        return chunk

    return new
