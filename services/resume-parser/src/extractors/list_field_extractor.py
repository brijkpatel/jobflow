"""Generic list extractor for simple string-list fields.

Used for: interests, languages, awards.
"""

from typing import List

from interfaces import FieldExtractor, ExtractionStrategy, FieldType
from exceptions import FieldExtractionError
from utils import logger


class ListFieldExtractor(FieldExtractor[List[str]]):
    """Extract a flat list of strings for simple multi-value fields.

    Handles interests, languages, and awards — fields where the LLM
    returns a plain JSON array of strings.
    """

    def __init__(
        self,
        extraction_strategy: ExtractionStrategy[List[str]],
        field_type: FieldType,
    ):
        """Initialize with strategy and target field type.

        Args:
            extraction_strategy: Strategy to use for extraction
            field_type: The field being extracted (for logging)
        """
        self.extraction_strategy = extraction_strategy
        self.field_type = field_type

    def extract(self, text: str) -> List[str]:
        """Extract list of values from text.

        Args:
            text: Resume text

        Returns:
            List of extracted strings (may be empty)

        Raises:
            FieldExtractionError: On extraction failure
        """
        text = text.strip()
        if not text:
            raise FieldExtractionError(
                f"Input text is empty for {self.field_type.value}"
            )

        try:
            results = self.extraction_strategy.extract(text)
            items = [r.strip() for r in results if r and r.strip()]
            logger.debug(
                f"Extracted {len(items)} items for {self.field_type.value}"
            )
            return items
        except FieldExtractionError:
            raise
        except Exception as e:
            raise FieldExtractionError(
                f"{self.field_type.value} extraction failed", original_exception=e
            ) from e
