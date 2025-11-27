from __future__ import annotations

from typing import Any, AsyncIterator, Iterable

from .chunk import extract_text, inject_text
from .log import log
from .registry import register
from .runtime import get_state


@register("content_filter")
class ContentFilter:
    def __init__(
        self,
        terms: Iterable[str] | None = None,
        replacement: str = "CONTENT FILTERED",
    ) -> None:
        terms = list(terms or ["fail"])
        if not terms:
            raise ValueError("content_filter requires at least one term")
        self._terms = [term.lower() for term in terms]
        self.replacement = replacement

    def install(self, agent: Any, **_: Any) -> None:
        state = get_state(agent)
        state.helpers.content_filter_terms = tuple(self._terms)

        async def processor(stream: AsyncIterator[Any]) -> AsyncIterator[Any]:
            async for chunk in stream:
                try:
                    text = extract_text(chunk)
                    if text is None:
                        yield chunk
                        continue

                    lowered = text.lower()
                    if any(term in lowered for term in self._terms):
                        yield inject_text(chunk, self.replacement)
                    else:
                        yield chunk
                except Exception:
                    log.exception("content_filter processor error")
                    yield chunk

        state.pipeline.add(processor)
