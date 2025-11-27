from __future__ import annotations

from typing import Any, Dict, Type

from .base import Extension

_REGISTRY: Dict[str, Type[Any]] = {}


def register(name: str):
    """Decorator to register an extension class with ``name``."""

    def decorator(cls: Type[Any]):
        if name in _REGISTRY:
            raise ValueError(f"extension '{name}' already registered")
        _REGISTRY[name] = cls
        setattr(cls, "name", name)
        return cls

    return decorator


def create(name: str, **cfg: Any) -> Extension:
    try:
        ext_cls = _REGISTRY[name]
    except KeyError as exc:
        raise KeyError(f"extension '{name}' is not registered") from exc
    return ext_cls(**cfg)  # type: ignore[return-value]


def registry() -> Dict[str, Type[Any]]:
    return dict(_REGISTRY)
