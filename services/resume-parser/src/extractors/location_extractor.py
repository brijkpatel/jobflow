"""Extract location (city/country) from resume text."""

from typing import List

from interfaces import FieldExtractor, ExtractionStrategy
from exceptions import FieldExtractionError
from utils import logger


class LocationExtractor(FieldExtractor[str]):
    """Extract location using configured strategy (NER or LLM)."""

    def __init__(self, extraction_strategy: ExtractionStrategy[List[str]]):
        """Initialize with extraction strategy."""
        self.extraction_strategy = extraction_strategy

    def extract(self, text: str) -> str:
        """Extract location from text.

        Args:
            text: Resume text

        Returns:
            Location string

        Raises:
            FieldExtractionError: If no location found
        """
        text = text.strip()
        if not text:
            raise FieldExtractionError("Input text is empty")

        try:
            results = self.extraction_strategy.extract(text)
            if not results:
                raise FieldExtractionError("No location found")
            location = results[0].strip()
            logger.debug(f"Extracted location: {location}")
            return location
        except FieldExtractionError:
            raise
        except Exception as e:
            raise FieldExtractionError(
                "Location extraction failed", original_exception=e
            ) from e
