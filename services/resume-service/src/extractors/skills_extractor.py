"""Extract skills list from resume text."""

from typing import List

from interfaces import FieldExtractor, ExtractionStrategy
from exceptions import FieldExtractionError


class SkillsExtractor(FieldExtractor[List[str]]):
    """Extract list of skills using configured strategy."""

    def __init__(self, extraction_strategy: ExtractionStrategy[List[str]]):
        """Initialize with extraction strategy (NER or LLM)."""
        self.extraction_strategy = extraction_strategy

    def extract(self, text: str) -> List[str]:
        """Extract skills from text.

        Steps:
            1. Validate input text
            2. Run extraction strategy
            3. Return list of skills

        Args:
            text: Resume text

        Returns:
            List of skills

        Raises:
            FieldExtractionError: If no skills found
        """
        processed_text = self.validate_input(text)

        try:
            skills = self.extraction_strategy.extract(processed_text)
            if not skills:
                raise FieldExtractionError("No skills found")
            return skills
        except Exception as e:
            raise FieldExtractionError(
                "Skills extraction failed", original_exception=e
            ) from e

    def validate_input(self, text: str) -> str:
        """Check text is long enough."""
        text = text.strip()
        if len(text) < 2:
            raise FieldExtractionError(
                "Input text must be at least 2 characters long after stripping"
            )
        return text
