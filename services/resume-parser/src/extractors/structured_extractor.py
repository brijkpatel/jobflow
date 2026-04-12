"""Base class for extractors that deserialise LLM-produced JSON object strings."""

import json
from abc import ABC, abstractmethod
from typing import Generic, List, TypeVar

from interfaces import ExtractionStrategy
from exceptions import FieldExtractionError
from utils import logger

T = TypeVar("T")


class StructuredExtractor(ABC, Generic[T]):
    """Base for extractors that receive JSON-string lists from the LLM and parse
    them into typed dataclass instances.

    Subclasses must implement:
        _parse_item(data: dict) -> T   — convert a single parsed dict to a dataclass
        _field_name() -> str           — human-readable field name for error messages
    """

    def __init__(self, extraction_strategy: ExtractionStrategy[List[str]]):
        """Initialize with an LLM (structured) extraction strategy."""
        self.extraction_strategy = extraction_strategy

    def extract(self, text: str) -> List[T]:
        """Extract and deserialise structured entries from resume text.

        Steps:
            1. Validate input
            2. Call strategy (returns list of JSON strings)
            3. Parse each JSON string into a typed dataclass
            4. Return list of dataclass instances

        Args:
            text: Resume text

        Returns:
            List of typed dataclass instances

        Raises:
            FieldExtractionError: On extraction or parsing failure
        """
        text = text.strip()
        if not text:
            raise FieldExtractionError(f"Input text is empty for {self._field_name()}")

        try:
            json_strings = self.extraction_strategy.extract(text)
        except Exception as e:
            raise FieldExtractionError(
                f"{self._field_name()} LLM extraction failed", original_exception=e
            ) from e

        results: List[T] = []
        for raw in json_strings:
            try:
                data = json.loads(raw) if isinstance(raw, str) else raw
                item = self._parse_item(data)
                results.append(item)
            except Exception as e:
                logger.warning(
                    f"Skipping malformed {self._field_name()} entry: {e} | raw={raw!r}"
                )
                continue

        logger.debug(f"Extracted {len(results)} {self._field_name()} entries")
        return results

    @abstractmethod
    def _parse_item(self, data: dict) -> T:
        """Convert a parsed JSON dict into a typed dataclass instance."""
        raise NotImplementedError

    @abstractmethod
    def _field_name(self) -> str:
        """Human-readable name used in log/error messages."""
        raise NotImplementedError
