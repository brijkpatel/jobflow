from __future__ import annotations

import re


class RegexExtractionStrategy:
    def __init__(self, *patterns: str) -> None:
        if not patterns:
            raise ValueError("at least one regex pattern is required")
        self._patterns = [re.compile(pattern, re.IGNORECASE | re.MULTILINE) for pattern in patterns]

    def extract(self, text: str) -> str | None:
        for pattern in self._patterns:
            match = pattern.search(text)
            if match:
                value = match.group(1) if match.groups() else match.group(0)
                cleaned = value.strip()
                if cleaned:
                    return cleaned
        return None
