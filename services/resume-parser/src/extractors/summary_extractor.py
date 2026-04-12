"""Extract professional summary / objective from resume text."""

from typing import List

from interfaces import FieldExtractor, ExtractionStrategy
from exceptions import FieldExtractionError
from utils import logger


class SummaryExtractor(FieldExtractor[str]):
    """Extract the professional summary or objective statement (LLM strategy)."""

    def __init__(self, extraction_strategy: ExtractionStrategy[List[str]]):
        """Initialize with extraction strategy."""
        self.extraction_strategy = extraction_strategy

    def extract(self, text: str) -> str:
        """Extract summary from text.

        Args:
            text: Resume text

        Returns:
            Summary/objective string

        Raises:
            FieldExtractionError: If no summary found
        """
        text = text.strip()
        if not text:
            raise FieldExtractionError("Input text is empty")

        try:
            results = self.extraction_strategy.extract(text)
            if not results:
                raise FieldExtractionError("No summary found")
            summary = results[0].strip()
            logger.debug(f"Extracted summary ({len(summary)} chars)")
            return summary
        except FieldExtractionError:
            raise
        except Exception as e:
            raise FieldExtractionError(
                "Summary extraction failed", original_exception=e
            ) from e
