from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Extension(Protocol):
    """Protocol describing a lightweight extension."""

    name: str

    def install(self, agent: Any, **config: Any) -> None:
        """Install the extension onto ``agent``."""
