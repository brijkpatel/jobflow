"""Extract fields using regular expressions."""

import re
from typing import List

from interfaces import ExtractionStrategy, FieldSpec
from exceptions import InvalidStrategyConfigError, NoMatchFoundError


class RegexExtractionStrategy(ExtractionStrategy[List[str]]):
    """Extract using regex patterns (fast, works well for emails)."""

    def __init__(self, spec: FieldSpec):
        """Initialize with regex patterns from spec.

        Args:
            spec: Field specification with regex_patterns

        Raises:
            InvalidStrategyConfigError: If no patterns provided
        """
        self.spec = spec
        if not self.spec.regex_patterns:
            raise InvalidStrategyConfigError(
                "At least one regex pattern must be provided"
            )

        # Compile patterns
        self.patterns: List[re.Pattern[str]] = []
        for pattern in self.spec.regex_patterns:
            try:
                self.patterns.append(re.compile(pattern, re.IGNORECASE | re.MULTILINE))
            except re.error as e:
                raise InvalidStrategyConfigError(
                    "Invalid regex pattern", original_exception=e
                ) from e

    def extract(self, text: str) -> List[str]:
        """Extract field using regex.

        Steps:
            1. Try each pattern in order
            2. Return matches from first pattern that succeeds
            3. Respect top_k limit if specified

        Args:
            text: Text to search

        Returns:
            List of matches

        Raises:
            NoMatchFoundError: If no pattern matches
        """
        if not text or not text.strip():
            raise NoMatchFoundError("Cannot extract from empty text")

        # Try each pattern
        for pattern in self.patterns:
            matches = pattern.findall(text)
            if matches:
                # Flatten tuples from capture groups
                if matches and isinstance(matches[0], tuple):
                    matches = [m for match in matches for m in match if m]

                # Apply limit
                if self.spec.top_k is not None:
                    return (
                        matches[: self.spec.top_k] if self.spec.top_k > 0 else matches
                    )
                else:
                    return [matches[0]] if matches else []

        raise NoMatchFoundError(
            f"No matches found for field '{self.spec.field_type.value}' using {len(self.patterns)} patterns"
        )
