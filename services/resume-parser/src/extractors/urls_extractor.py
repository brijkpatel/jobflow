"""Extract specific URL types from resume text (LinkedIn, GitHub, Portfolio, Other)."""

from typing import List

from interfaces import FieldExtractor, ExtractionStrategy, FieldType
from exceptions import FieldExtractionError
from utils import logger


class UrlsExtractor(FieldExtractor[List[str]]):
    """Extract URLs of a specific type using configured strategy (Regex or LLM).

    A single extractor class handles all URL field types. The field_type passed
    at construction determines which kind of URL is targeted (LinkedIn, GitHub,
    Portfolio, or Other).
    """

    def __init__(
        self,
        extraction_strategy: ExtractionStrategy[List[str]],
        field_type: FieldType,
    ):
        """Initialize with strategy and target URL field type.

        Args:
            extraction_strategy: Strategy to use for extraction
            field_type: One of LINKEDIN_URL, GITHUB_URL, PORTFOLIO_URL, OTHER_URLS
        """
        self.extraction_strategy = extraction_strategy
        self.field_type = field_type

    def extract(self, text: str) -> List[str]:
        """Extract URLs from text.

        Args:
            text: Resume text

        Returns:
            List of URL strings (may be empty)

        Raises:
            FieldExtractionError: On extraction failure
        """
        text = text.strip()
        if not text:
            raise FieldExtractionError("Input text is empty")

        try:
            results = self.extraction_strategy.extract(text)
            urls = [u.strip() for u in results if u and u.strip()]
            logger.debug(f"Extracted {len(urls)} URL(s) for {self.field_type.value}")
            return urls
        except FieldExtractionError:
            raise
        except Exception as e:
            raise FieldExtractionError(
                f"URL extraction failed for {self.field_type.value}",
                original_exception=e,
            ) from e
