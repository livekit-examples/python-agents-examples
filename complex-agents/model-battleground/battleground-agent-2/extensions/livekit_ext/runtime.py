from __future__ import annotations

import inspect
from collections.abc import AsyncIterable, AsyncIterator
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any

from .base import Extension
from .log import log
from .pipeline import Pipeline


@dataclass
class ExtensionState:
    helpers: Any
    pipeline: Pipeline = field(default_factory=Pipeline)
    installed: list[Extension] = field(default_factory=list)


def get_state(agent: Any) -> ExtensionState:
    """Return (and create if needed) the extension state for ``agent``."""

    state = getattr(agent, "_livekit_extensions", None)
    if state is None:
        helpers = getattr(agent, "helpers", None)
        if helpers is None:
            helpers = SimpleNamespace()
            setattr(agent, "helpers", helpers)
        state = ExtensionState(helpers=helpers)
        setattr(agent, "_livekit_extensions", state)
        setattr(agent, "extensions", state)
    return state


def ensure_helpers(agent: Any) -> Any:
    """Backward-compatible helper namespace accessor."""

    return get_state(agent).helpers


ExtensionSpec = Any


def _resolve_extension(spec: ExtensionSpec) -> Extension:
    if spec is None:
        raise TypeError("extension spec cannot be None")

    if inspect.isclass(spec):
        # Accept extension classes.
        instance = spec()
        if not hasattr(instance, "install"):
            raise TypeError("extension class must define install()")
        return instance

    if callable(spec) and not hasattr(spec, "install"):
        candidate = spec()
        if not hasattr(candidate, "install"):
            raise TypeError("extension factory must return an Extension")
        return candidate

    if hasattr(spec, "install"):
        return spec

    raise TypeError(
        "install_extensions expects extension objects, classes, or factories; "
        f"got {spec!r}"
    )


def _ensure_async_iterator(value: Any) -> AsyncIterator[Any]:
    """Convert various types to AsyncIterator."""
    if isinstance(value, AsyncIterator):
        return value
    if isinstance(value, AsyncIterable):
        async def _wrap() -> AsyncIterator[Any]:
            async for chunk in value:
                yield chunk
        return _wrap()

    async def _single() -> AsyncIterator[Any]:
        if value is not None:
            yield value
    return _single()


def _patch_llm_node(agent: Any, state: ExtensionState) -> None:
    """Automatically patch the agent's llm_node method to integrate the pipeline."""
    
    # Check if already patched
    if hasattr(agent, "_livekit_ext_original_llm_node"):
        return
    
    # Check if llm_node exists
    if not hasattr(agent, "llm_node"):
        log.warning("Agent does not have llm_node method")
        return
    
    # Store the original method
    original_llm_node = agent.llm_node
    setattr(agent, "_livekit_ext_original_llm_node", original_llm_node)
    
    # Create wrapper that integrates the pipeline
    async def patched_llm_node(chat_ctx, tools, model_settings=None):
        # Call original llm_node
        result = original_llm_node(chat_ctx, tools, model_settings)
        if inspect.isawaitable(result):
            result = await result
        
        # If no pipeline, return as-is
        if not state.pipeline:
            return result
        
        # Process through pipeline
        return state.pipeline.process(_ensure_async_iterator(result))
    
    # Replace the method
    agent.llm_node = patched_llm_node


def install_extensions(agent: Any, *extensions: ExtensionSpec) -> list[Extension]:
    """Install one or more extensions on ``agent``."""

    state = get_state(agent)
    installed: list[Extension] = []

    for spec in extensions:
        try:
            extension = _resolve_extension(spec)
        except Exception:
            log.exception("failed to resolve extension", extra={"extension": repr(spec)})
            continue

        try:
            extension.install(agent)
        except Exception:
            name = getattr(extension, "name", extension.__class__.__name__)
            log.exception("extension install failed", extra={"extension": name})
            continue

        state.installed.append(extension)
        installed.append(extension)

    # Automatically patch llm_node if extensions were installed
    if installed:
        _patch_llm_node(agent, state)

    return installed
