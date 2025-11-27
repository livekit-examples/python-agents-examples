from __future__ import annotations

from typing import Any, AsyncIterator

from .chunk import extract_text, inject_text
from .log import log
from .registry import register
from .runtime import get_state


@register("deepseek_think")
class DeepseekThink:
    def __init__(self, ready_phrase: str = "Okay, I'm ready to respond.") -> None:
        self.ready_phrase = ready_phrase

    def install(self, agent: Any, **_: Any) -> None:
        state = get_state(agent)

        async def processor(stream: AsyncIterator[Any]) -> AsyncIterator[Any]:
            async for chunk in stream:
                try:
                    text = extract_text(chunk)
                    if text is None:
                        yield chunk
                        continue

                    sanitized = text.replace("<think>", "")
                    if "</think>" in sanitized:
                        sanitized = sanitized.replace("</think>", self.ready_phrase)

                    if sanitized == text:
                        yield chunk
                    else:
                        yield inject_text(chunk, sanitized)
                except Exception:
                    log.exception("deepseek_think processor error")
                    yield chunk

        state.pipeline.add(processor)
