"""Field types, strategy types, and extraction interfaces."""

from dataclasses import dataclass
from typing import Optional, Generic, TypeVar, List
from abc import ABC, abstractmethod
from enum import Enum

T = TypeVar("T")
I = TypeVar("I")  # Input type for computed extractors


class FieldType(Enum):
    """Fields that can be extracted from resumes."""

    # Core identity
    NAME = "name"
    EMAIL = "email"
    SKILLS = "skills"

    # Contact information
    PHONE = "phone"
    LOCATION = "location"
    LINKEDIN_URL = "linkedin_url"
    GITHUB_URL = "github_url"
    PORTFOLIO_URL = "portfolio_url"
    OTHER_URLS = "other_urls"

    # Professional narrative
    SUMMARY = "summary"

    # Structured sections
    WORK_EXPERIENCE = "work_experience"
    EDUCATION = "education"
    CERTIFICATIONS = "certifications"
    PROJECTS = "projects"

    # Personal
    INTERESTS = "interests"
    LANGUAGES = "languages"
    AWARDS = "awards"

    # Optional sections
    VOLUNTEER_EXPERIENCE = "volunteer_experience"
    PUBLICATIONS = "publications"


class StrategyType(Enum):
    """Extraction strategies available."""

    REGEX = "regex"
    NER = "ner"
    LLM = "llm"


@dataclass(frozen=True)
class FieldSpec:
    """Configuration for what and how to extract.

    Attributes:
        field_type: What to extract
        regex_patterns: Patterns for regex strategy
        entity_label: Label for NER strategy (e.g., "person")
        top_k: Number limit (None = single value, 0 = unlimited, N = max N)
        is_structured: True when the LLM should return an array of JSON objects
                       rather than an array of plain strings. The extractor is
                       responsible for deserialising those objects.
    """

    field_type: FieldType
    regex_patterns: Optional[List[str]] = None
    entity_label: Optional[str] = None
    top_k: Optional[int] = None
    is_structured: bool = False


class ExtractionStrategy(ABC, Generic[T]):
    """Base class for all extraction strategies."""

    def __init__(self, spec: FieldSpec) -> None:
        """Initialize with field specification."""
        self.spec = spec

    @abstractmethod
    def extract(self, text: str) -> T:
        """Extract field from text."""
        raise NotImplementedError


class ComputedFieldExtractor(ABC, Generic[T, I]):
    """Base class for extractors that compute their result from prior extractions.

    Unlike FieldExtractor (which works from raw text), a ComputedFieldExtractor
    derives its output from already-extracted structured data.

    Type parameters:
        T: Return type of compute()
        I: Input type (e.g., List[WorkExperienceEntry])
    """

    @abstractmethod
    def compute(self, data: I) -> T:
        """Compute the field value from previously extracted data.

        Args:
            data: Previously extracted structured data

        Returns:
            Computed field value
        """
        raise NotImplementedError
