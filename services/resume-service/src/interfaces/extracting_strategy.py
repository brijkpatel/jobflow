"""Field types, strategy types, and extraction interfaces."""

from dataclasses import dataclass
from typing import Optional, Generic, TypeVar, List
from abc import ABC, abstractmethod
from enum import Enum

T = TypeVar("T")


class FieldType(Enum):
    """Fields that can be extracted from resumes."""

    NAME = "name"
    EMAIL = "email"
    SKILLS = "skills"


class StrategyType(Enum):
    """Extraction strategies available."""

    REGEX = "regex"
    NER = "ner"
    LLM = "llm"


@dataclass(frozen=True)
class FieldSpec:
    """Configuration for what and how to extract.

    Attributes:
        field_type: What to extract (name, email, skills)
        regex_patterns: Patterns for regex strategy
        entity_label: Label for NER strategy (e.g., "person")
        top_k: Number limit (None = single value, 0 = unlimited, N = max N)
    """

    field_type: FieldType
    regex_patterns: Optional[List[str]] = None
    entity_label: Optional[str] = None
    top_k: Optional[int] = None


class ExtractionStrategy(ABC, Generic[T]):
    """Base class for all extraction strategies."""

    def __init__(self, spec: FieldSpec) -> None:
        """Initialize with field specification."""
        self.spec = spec

    @abstractmethod
    def extract(self, text: str) -> T:
        """Extract field from text."""
        raise NotImplementedError
