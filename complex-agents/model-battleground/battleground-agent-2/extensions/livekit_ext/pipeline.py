from __future__ import annotations

from typing import Any, AsyncIterator, Callable, Iterable

from .log import log

Processor = Callable[[AsyncIterator[Any]], AsyncIterator[Any]]


async def _run_processor(processor: Processor, source: AsyncIterator[Any]) -> AsyncIterator[Any]:
    try:
        async for chunk in processor(source):
            yield chunk
    except Exception:
        log.exception(
            "processor failed, falling back to passthrough",
            extra={"processor": getattr(processor, "__name__", repr(processor))},
        )
        async for chunk in source:
            yield chunk


class Pipeline:
    """Composable collection of stream processors."""

    def __init__(self) -> None:
        self._processors: list[Processor] = []

    def add(self, processor: Processor) -> None:
        self._processors.append(processor)

    def extend(self, processors: Iterable[Processor]) -> None:
        self._processors.extend(processors)

    def clear(self) -> None:
        self._processors.clear()

    def __bool__(self) -> bool:
        return bool(self._processors)

    @property
    def processors(self) -> tuple[Processor, ...]:
        return tuple(self._processors)

    async def process(self, base_stream: AsyncIterator[Any]) -> AsyncIterator[Any]:
        if not self._processors:
            async for chunk in base_stream:
                yield chunk
            return

        wrapped: AsyncIterator[Any] = base_stream
        for processor in self._processors:
            wrapped = _run_processor(processor, wrapped)

        async for chunk in wrapped:
            yield chunk
