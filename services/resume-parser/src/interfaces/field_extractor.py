"""Base class for field extractors."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar


T = TypeVar("T")  # Generic type for extraction result


class FieldExtractor(ABC, Generic[T]):
    """Base class for extracting fields from text.

    Implemented by: NameExtractor, EmailExtractor, SkillsExtractor

    Type T is the return type:
        - str for name and email
        - List[str] for skills
    """

    @abstractmethod
    def extract(self, text: str) -> T:
        """Extract field from text.

        Args:
            text: Resume text

        Returns:
            Extracted value (type depends on field)

        Raises:
            FieldExtractionError: If extraction fails
        """
