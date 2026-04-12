"""Create field extractors with appropriate strategies."""

from typing import Dict, List, Union, Any

from interfaces import (
    FieldExtractor,
    FieldSpec,
    FieldType,
    StrategyType,
    ExtractionStrategy,
)
from .name_extractor import NameExtractor
from .email_extractor import EmailExtractor
from .skills_extractor import SkillsExtractor
from .phone_extractor import PhoneExtractor
from .location_extractor import LocationExtractor
from .urls_extractor import UrlsExtractor
from .summary_extractor import SummaryExtractor
from .work_experience_extractor import WorkExperienceExtractor
from .education_extractor import EducationExtractor
from .certifications_extractor import CertificationsExtractor
from .projects_extractor import ProjectsExtractor
from .volunteer_extractor import VolunteerExtractor
from .publications_extractor import PublicationsExtractor
from .list_field_extractor import ListFieldExtractor
from .strategies.regex import RegexExtractionStrategy
from .strategies.ner import NERExtractionStrategy
from .strategies.llm import LLMExtractionStrategy
from exceptions import InvalidStrategyConfigError


# Regex patterns for phone numbers (covers most international formats)
_PHONE_PATTERNS = [
    r"(?:(?:\+|00)\d{1,3}[\s\-\.]?)?"          # optional country code
    r"(?:\(?\d{1,4}\)?[\s\-\.]?)?"              # optional area code
    r"\d{3,4}[\s\-\.]\d{3,5}"                   # core number
    r"(?:[\s\-\.]\d{1,5})?",                    # optional extension
    r"\+?\d[\d\s\-\.\(\)]{7,20}\d",             # broad fallback
]

# Regex patterns for URLs
_URL_PATTERNS = [
    r"https?://[^\s\]\)\>\"\']+",
    r"(?<!\w)(?:www\.)[^\s\]\)\>\"\']+",
]

# Patterns scoped per URL field type
_LINKEDIN_PATTERNS = [r"(?:https?://)?(?:www\.)?linkedin\.com/in/[^\s\]\)\>\"\']+"]
_GITHUB_PATTERNS = [r"(?:https?://)?(?:www\.)?github\.com/[^\s\]\)\>\"\']+"]


# Which strategies are valid for each field type
SUPPORTED_STRATEGIES: Dict[FieldType, List[StrategyType]] = {
    FieldType.NAME: [StrategyType.NER, StrategyType.LLM],
    FieldType.EMAIL: [StrategyType.REGEX, StrategyType.NER, StrategyType.LLM],
    FieldType.SKILLS: [StrategyType.NER, StrategyType.LLM],
    FieldType.PHONE: [StrategyType.REGEX, StrategyType.LLM],
    FieldType.LOCATION: [StrategyType.NER, StrategyType.LLM],
    FieldType.LINKEDIN_URL: [StrategyType.REGEX, StrategyType.LLM],
    FieldType.GITHUB_URL: [StrategyType.REGEX, StrategyType.LLM],
    FieldType.PORTFOLIO_URL: [StrategyType.REGEX, StrategyType.LLM],
    FieldType.OTHER_URLS: [StrategyType.REGEX, StrategyType.LLM],
    FieldType.SUMMARY: [StrategyType.LLM],
    FieldType.WORK_EXPERIENCE: [StrategyType.LLM],
    FieldType.EDUCATION: [StrategyType.LLM],
    FieldType.CERTIFICATIONS: [StrategyType.LLM],
    FieldType.PROJECTS: [StrategyType.LLM],
    FieldType.INTERESTS: [StrategyType.LLM],
    FieldType.LANGUAGES: [StrategyType.LLM],
    FieldType.AWARDS: [StrategyType.LLM],
    FieldType.VOLUNTEER_EXPERIENCE: [StrategyType.LLM],
    FieldType.PUBLICATIONS: [StrategyType.LLM],
}


def create_extractor(
    field_type: FieldType,
    strategy_type: StrategyType,
) -> FieldExtractor[Any]:
    """Create extractor for a field using the specified strategy.

    Steps:
        1. Validate strategy is supported for the field
        2. Build FieldSpec
        3. Build strategy instance
        4. Wrap in the appropriate FieldExtractor
        5. Return

    Args:
        field_type: Field to extract
        strategy_type: Strategy to use

    Returns:
        Configured, ready-to-use extractor

    Raises:
        InvalidStrategyConfigError: If the combination is not supported
    """
    supported = SUPPORTED_STRATEGIES.get(field_type, [])
    if strategy_type not in supported:
        raise InvalidStrategyConfigError(
            f"Strategy '{strategy_type.value}' is not supported for field '{field_type.value}'. "
            f"Supported: {[s.value for s in supported]}"
        )

    spec = _create_field_spec(field_type)
    strategy = _create_strategy(field_type, strategy_type, spec)
    return _create_field_extractor(field_type, strategy)


def _create_field_spec(field_type: FieldType) -> FieldSpec:
    """Build a FieldSpec for the given field type."""

    # Structured fields return JSON objects from the LLM
    _structured = {
        FieldType.WORK_EXPERIENCE,
        FieldType.EDUCATION,
        FieldType.CERTIFICATIONS,
        FieldType.PROJECTS,
        FieldType.VOLUNTEER_EXPERIENCE,
        FieldType.PUBLICATIONS,
    }

    # Fields returning a single scalar value
    _scalar = {
        FieldType.NAME,
        FieldType.EMAIL,
        FieldType.PHONE,
        FieldType.LOCATION,
        FieldType.LINKEDIN_URL,
        FieldType.GITHUB_URL,
        FieldType.PORTFOLIO_URL,
        FieldType.SUMMARY,
    }

    is_structured = field_type in _structured
    top_k = None if field_type in _scalar else 0

    # Regex patterns for fields that support regex
    regex_map: Dict[FieldType, List[str]] = {
        FieldType.EMAIL: [r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"],
        FieldType.PHONE: _PHONE_PATTERNS,
        FieldType.LINKEDIN_URL: _LINKEDIN_PATTERNS,
        FieldType.GITHUB_URL: _GITHUB_PATTERNS,
        FieldType.PORTFOLIO_URL: _URL_PATTERNS,
        FieldType.OTHER_URLS: _URL_PATTERNS,
    }

    entity_map: Dict[FieldType, str] = {
        FieldType.NAME: "person",
        FieldType.EMAIL: "email",
        FieldType.SKILLS: "skill",
        FieldType.LOCATION: "location",
    }

    return FieldSpec(
        field_type=field_type,
        regex_patterns=regex_map.get(field_type),
        entity_label=entity_map.get(field_type),
        top_k=top_k,
        is_structured=is_structured,
    )


def _create_strategy(
    field_type: FieldType,
    strategy_type: StrategyType,
    spec: FieldSpec,
) -> ExtractionStrategy[List[str]]:
    """Instantiate the requested strategy."""
    if strategy_type == StrategyType.REGEX:
        if not spec.regex_patterns:
            raise InvalidStrategyConfigError(
                f"No regex patterns configured for '{field_type.value}'"
            )
        return RegexExtractionStrategy(spec)

    if strategy_type == StrategyType.NER:
        return NERExtractionStrategy(spec)

    if strategy_type == StrategyType.LLM:
        return LLMExtractionStrategy(spec)

    raise InvalidStrategyConfigError(f"Unknown strategy type: {strategy_type}")


def _create_field_extractor(
    field_type: FieldType,
    strategy: ExtractionStrategy[List[str]],
) -> FieldExtractor[Any]:
    """Wrap the strategy in the appropriate FieldExtractor subclass."""
    match field_type:
        case FieldType.NAME:
            return NameExtractor(strategy)
        case FieldType.EMAIL:
            return EmailExtractor(strategy)
        case FieldType.SKILLS:
            return SkillsExtractor(strategy)
        case FieldType.PHONE:
            return PhoneExtractor(strategy)
        case FieldType.LOCATION:
            return LocationExtractor(strategy)
        case FieldType.LINKEDIN_URL | FieldType.GITHUB_URL | FieldType.PORTFOLIO_URL | FieldType.OTHER_URLS:
            return UrlsExtractor(strategy, field_type)
        case FieldType.SUMMARY:
            return SummaryExtractor(strategy)
        case FieldType.WORK_EXPERIENCE:
            return WorkExperienceExtractor(strategy)
        case FieldType.EDUCATION:
            return EducationExtractor(strategy)
        case FieldType.CERTIFICATIONS:
            return CertificationsExtractor(strategy)
        case FieldType.PROJECTS:
            return ProjectsExtractor(strategy)
        case FieldType.VOLUNTEER_EXPERIENCE:
            return VolunteerExtractor(strategy)
        case FieldType.PUBLICATIONS:
            return PublicationsExtractor(strategy)
        case FieldType.INTERESTS | FieldType.LANGUAGES | FieldType.AWARDS:
            return ListFieldExtractor(strategy, field_type)
        case _:
            raise InvalidStrategyConfigError(f"No extractor defined for field '{field_type.value}'")
