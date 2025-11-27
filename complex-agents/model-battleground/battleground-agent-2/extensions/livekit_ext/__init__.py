"""Lightweight extension helpers for LiveKit agent examples."""

from .base import Extension
from .registry import register, create, registry
from .runtime import get_state, install_extensions, ensure_helpers
from .rpc import RPC, rpc_call
from .context_augmented_generation import ContextAugmentedGeneration
from .image_processor import ImageProcessor

__all__ = [
    "Extension",
    "register",
    "create",
    "registry",
    "get_state",
    "install_extensions",
    "ensure_helpers",
    "RPC",
    "rpc_call",
    "ContextAugmentedGeneration",
    "ImageProcessor",
]

__version__ = "0.1.0"
