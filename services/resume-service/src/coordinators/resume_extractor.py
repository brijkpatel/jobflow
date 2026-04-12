"""Orchestrates extraction of name, email, and skills from resume text."""

from typing import Dict, List, Any, Optional
from interfaces import FieldExtractor, FieldType
from models import ResumeData
from utils import logger


class ResumeExtractor:
    """Runs multiple extractors for each field with automatic fallback.

    How it works:
        - Each field (name, email, skills) has a list of extractors
        - Tries extractors in order until one succeeds
        - Returns None if all extractors fail for a field

    Example:
        For email: tries Regex → NER → LLM
        If Regex succeeds, returns immediately
        If Regex fails, tries NER, and so on
    """

    def __init__(
        self,
        extractors: Dict[FieldType, List[FieldExtractor[Any]]],
    ):
        """Initialize with extractors for each field type.

        Args:
            extractors: Dict mapping field types to list of extractors
                       Extractors are tried in order

        Raises:
            ValueError: If extractors missing or incomplete
        """
        if not extractors:
            raise ValueError("extractors dictionary cannot be None or empty")

        # Check all required fields are present
        required_fields = {FieldType.NAME, FieldType.EMAIL, FieldType.SKILLS}
        provided_fields = set(extractors.keys())

        if not required_fields.issubset(provided_fields):
            missing = required_fields - provided_fields
            raise ValueError(
                f"Missing required field types: {[f.value for f in missing]}"
            )

        self.extractors: Dict[FieldType, List[FieldExtractor[Any]]] = extractors

        logger.info(
            f"ResumeExtractor initialized with extractors for "
            f"{len(extractors)} field types"
        )

    def extract(self, text: str) -> ResumeData:
        """Extract name, email, and skills from resume text.

        Steps:
            1. Validate text is not empty
            2. Extract each field using extractor chain
            3. Create ResumeData with results
            4. Return data (fields may be None if extraction failed)

        Args:
            text: Resume text to extract from

        Returns:
            ResumeData with extracted fields (may have None values)

        Raises:
            ValueError: If text is empty
        """
        if not text or not text.strip():
            raise ValueError("Resume text cannot be empty")

        logger.info("Starting field extraction from resume text")

        # Extract each field
        name = self._extract_field(FieldType.NAME, text)
        email = self._extract_field(FieldType.EMAIL, text)
        skills = self._extract_field(FieldType.SKILLS, text)

        # Create result object
        resume_data = ResumeData(name=name, email=email, skills=skills)
        logger.info("Successfully created ResumeData object")
        return resume_data

    def _extract_field(self, field_type: FieldType, text: str) -> Optional[Any]:
        """Try extractors in order until one succeeds.

        Args:
            field_type: Type of field to extract
            text: Text to extract from

        Returns:
            Extracted value or None if all fail (empty list for skills)
        """
        extractors = self.extractors.get(field_type, [])
        field_name = field_type.value

        logger.debug(
            f"Attempting to extract '{field_name}' using {len(extractors)} extractor(s)"
        )

        # Try each extractor
        for idx, extractor in enumerate(extractors, 1):
            try:
                logger.debug(
                    f"Trying extractor {idx}/{len(extractors)} for '{field_name}'"
                )
                result = extractor.extract(text)

                # Check if result is meaningful
                if result is not None and result != [] and result != "":
                    logger.info(
                        f"Successfully extracted '{field_name}' using {extractor.__class__.__name__} "
                        f"(strategy: {getattr(getattr(extractor, 'extraction_strategy', None), '__class__', type(None)).__name__})"
                    )
                    return result
                else:
                    logger.warning(
                        f"Extractor {idx} returned empty result for '{field_name}'"
                    )
            except Exception as e:
                logger.error(
                    f"Extractor {idx} failed for '{field_name}': {type(e).__name__}: {e}"
                )
                continue

        # All extractors failed
        logger.error(
            f"All {len(extractors)} extractor(s) failed for '{field_name}'. "
            f"Returning None/empty."
        )

        # Return appropriate default
        if field_type == FieldType.SKILLS:
            return []
        else:
            return None
