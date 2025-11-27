from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

from livekit.agents import inference
from livekit.agents.llm import ChatContext, ChatMessage

from .chunk import extract_text
from .log import log
from .registry import register
from .runtime import get_state


def _normalize_context(context: Any | Iterable[str]) -> str:
    if not context:
        return ""
    if isinstance(context, str):
        return context.strip()
    try:
        parts = [str(item).strip() for item in context if str(item).strip()]
    except TypeError:
        return str(context).strip()
    return "\n\n".join(parts)


class _ContextHelper:
    def __init__(
        self,
        *,
        model: str,
        system_prompt: str,
        llm_factory: Callable[[str], Any],
    ) -> None:
        self._model = model
        self._system_prompt = system_prompt
        self._llm_factory = llm_factory

    async def ask(self, question: str) -> str:
        if not question:
            return ""

        chat_ctx = ChatContext(
            [
                ChatMessage(
                    type="message",
                    role="system",
                    content=[self._system_prompt or "Use the provided context to answer."],
                ),
                ChatMessage(type="message", role="user", content=[question]),
            ]
        )

        try:
            async with self._llm_factory(self._model) as llm:
                response_chunks: list[str] = []
                async with llm.chat(chat_ctx=chat_ctx) as stream:
                    async for chunk in stream:
                        text = extract_text(chunk)
                        if text:
                            response_chunks.append(text)
            return "".join(response_chunks).strip()
        except Exception:
            log.exception("context augmented generation ask failed")
            raise


def _default_llm_factory(model: str) -> Any:
    return inference.LLM(model=model)


@register("context_augmented_generation")
class ContextAugmentedGeneration:
    def __init__(
        self,
        *,
        model: str,
        context: Any | Iterable[str],
        llm_factory: Callable[[str], Any] | None = None,
    ) -> None:
        self.model = model
        self.system_prompt = _normalize_context(context)
        self._llm_factory = llm_factory or _default_llm_factory

    def install(self, agent: Any, **_: Any) -> None:
        state = get_state(agent)
        state.helpers.context_augmented_generation = _ContextHelper(
            model=self.model,
            system_prompt=self.system_prompt,
            llm_factory=self._llm_factory,
        )
