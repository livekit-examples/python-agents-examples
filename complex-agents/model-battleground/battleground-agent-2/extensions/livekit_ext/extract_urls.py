from __future__ import annotations

import re
from typing import Any

from .registry import register
from .runtime import get_state

_URL_PATTERN = re.compile(r"https?://\S+")


@register("extract_urls")
class ExtractURLs:
    def install(self, agent: Any, **_: Any) -> None:
        state = get_state(agent)
        helpers = state.helpers

        def urls_from_text(text: str) -> list[str]:
            return _URL_PATTERN.findall(text)

        helpers.extract_urls = urls_from_text
