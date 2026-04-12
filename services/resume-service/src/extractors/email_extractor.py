"""Extract email address from resume text."""

import re
from typing import List

from interfaces import FieldExtractor, ExtractionStrategy
from exceptions import FieldExtractionError
from utils import logger


class EmailExtractor(FieldExtractor[str]):
    """Extract email address using configured strategy."""

    def __init__(self, extraction_strategy: ExtractionStrategy[List[str]]):
        """Initialize with extraction strategy (Regex, NER, or LLM)."""
        self.extraction_strategy = extraction_strategy

    def extract(self, text: str) -> str:
        """Extract email from text.

        Steps:
            1. Validate input text
            2. Run extraction strategy
            3. Validate email format
            4. Return email

        Args:
            text: Resume text

        Returns:
            Email address

        Raises:
            FieldExtractionError: If no valid email found
        """
        processed_text = self.validate_input(text)

        try:
            emails = self.extraction_strategy.extract(processed_text)
            if not emails:
                raise FieldExtractionError("No email addresses found")
            email = emails[0]
            logger.debug(f"Extracted email: {email}")
            self.validate_email_format(email)
            return email
        except Exception as e:
            raise FieldExtractionError(
                "Email extraction failed", original_exception=e
            ) from e

    def validate_input(self, text: str) -> str:
        """Check text is long enough to contain an email."""
        text = text.strip()
        if len(text) < 5:
            raise FieldExtractionError(
                "Input text must be at least 5 characters long after stripping"
            )
        return text

    def validate_email_format(self, email: str) -> None:
        """Check email format is valid."""
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email):
            raise FieldExtractionError(f"Invalid email format")
