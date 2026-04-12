"""Extract phone number from resume text."""

import re
from typing import List

from interfaces import FieldExtractor, ExtractionStrategy
from exceptions import FieldExtractionError
from utils import logger


class PhoneExtractor(FieldExtractor[str]):
    """Extract a phone number using configured strategy (Regex or LLM)."""

    # Basic sanity check — at least 7 digits
    _MIN_DIGITS = 7

    def __init__(self, extraction_strategy: ExtractionStrategy[List[str]]):
        """Initialize with extraction strategy."""
        self.extraction_strategy = extraction_strategy

    def extract(self, text: str) -> str:
        """Extract phone number from text.

        Args:
            text: Resume text

        Returns:
            Phone number string

        Raises:
            FieldExtractionError: If no valid phone number found
        """
        text = self._validate_input(text)

        try:
            results = self.extraction_strategy.extract(text)
            if not results:
                raise FieldExtractionError("No phone number found")

            phone = results[0].strip()
            self._validate_phone(phone)
            logger.debug(f"Extracted phone: {phone}")
            return phone
        except FieldExtractionError:
            raise
        except Exception as e:
            raise FieldExtractionError(
                "Phone extraction failed", original_exception=e
            ) from e

    def _validate_input(self, text: str) -> str:
        """Ensure input text is not empty."""
        text = text.strip()
        if not text:
            raise FieldExtractionError("Input text is empty")
        return text

    def _validate_phone(self, phone: str) -> None:
        """Check that extracted value contains enough digits to be a phone number."""
        digits = re.sub(r"\D", "", phone)
        if len(digits) < self._MIN_DIGITS:
            raise FieldExtractionError(
                f"Extracted value '{phone}' does not look like a phone number"
            )
