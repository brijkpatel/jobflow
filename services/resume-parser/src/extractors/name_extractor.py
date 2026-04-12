"""Extract name from resume text."""

from typing import List

from interfaces import FieldExtractor, ExtractionStrategy
from exceptions import FieldExtractionError


class NameExtractor(FieldExtractor[str]):
    """Extract person's name using configured strategy."""

    def __init__(self, extraction_strategy: ExtractionStrategy[List[str]]):
        """Initialize with extraction strategy (NER or LLM)."""
        self.extraction_strategy = extraction_strategy

    def extract(self, text: str) -> str:
        """Extract name from text.

        Steps:
            1. Validate input text
            2. Run extraction strategy
            3. Return first name found

        Args:
            text: Resume text

        Returns:
            Person's name

        Raises:
            FieldExtractionError: If no name found
        """
        processed_text = self.validate_input(text)

        try:
            names = self.extraction_strategy.extract(processed_text)
            if not names:
                raise FieldExtractionError("No names found")
            return names[0]
        except Exception as e:
            raise FieldExtractionError(
                "Name extraction failed", original_exception=e
            ) from e

    def validate_input(self, text: str) -> str:
        """Check text is not empty."""
        text = text.strip()
        if len(text) < 1:
            raise FieldExtractionError(
                "Input text must be at least 1 character long after stripping"
            )
        return text
