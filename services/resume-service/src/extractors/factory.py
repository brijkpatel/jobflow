"""Create field extractors with appropriate strategies."""

from typing import Dict, List, Union

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
from .strategies.regex import RegexExtractionStrategy
from .strategies.ner import NERExtractionStrategy
from .strategies.llm import LLMExtractionStrategy
from exceptions import InvalidStrategyConfigError


# Define which strategies are supported for each field type
SUPPORTED_STRATEGIES: Dict[FieldType, List[StrategyType]] = {
    FieldType.NAME: [StrategyType.NER, StrategyType.LLM],
    FieldType.EMAIL: [StrategyType.REGEX, StrategyType.NER, StrategyType.LLM],
    FieldType.SKILLS: [StrategyType.NER, StrategyType.LLM],
}


def create_extractor(
    field_type: FieldType,
    strategy_type: StrategyType,
) -> Union[FieldExtractor[str], FieldExtractor[List[str]]]:
    """Create extractor for a field using specified strategy.

    Steps:
        1. Check strategy is supported for this field
        2. Create field specification
        3. Create strategy instance (Regex/NER/LLM)
        4. Create extractor with strategy
        5. Return configured extractor

    Args:
        field_type: Field to extract (NAME, EMAIL, SKILLS)
        strategy_type: Strategy to use (REGEX, NER, LLM)

    Returns:
        Ready-to-use extractor

    Raises:
        InvalidStrategyConfigError: If strategy not supported
    """
    # Check if valid combination
    if strategy_type not in SUPPORTED_STRATEGIES[field_type]:
        raise InvalidStrategyConfigError("Strategy is not supported for field")

    # Create specs
    field_spec = _create_field_spec(field_type)

    # Create strategy based on strategy type
    strategy = _create_strategy(field_type, strategy_type, field_spec)

    # Create and return the appropriate extractor
    return _create_field_extractor(field_type, strategy)


def _create_field_spec(field_type: FieldType) -> FieldSpec:
    """Create spec for field (defines patterns, entity labels, etc)."""
    if field_type == FieldType.NAME:
        return FieldSpec(
            field_type=FieldType.NAME,
            entity_label="person",
            top_k=None,  # Single value
        )
    elif field_type == FieldType.EMAIL:
        return FieldSpec(
            field_type=field_type,
            regex_patterns=[r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"],
            entity_label="email",
            top_k=None,  # Single value
        )
    elif field_type == FieldType.SKILLS:
        return FieldSpec(
            field_type=field_type,
            entity_label="skill",
            top_k=0,  # Multiple values, no limit
        )
    else:
        raise InvalidStrategyConfigError(f"Unknown field type: {field_type}")


def _create_strategy(
    field_type: FieldType,
    strategy_type: StrategyType,
    field_spec: FieldSpec,
) -> ExtractionStrategy[List[str]]:
    """Create strategy instance (Regex, NER, or LLM)."""
    if strategy_type == StrategyType.REGEX:
        if not field_spec.regex_patterns:
            raise InvalidStrategyConfigError("Regex patterns not configured for field")
        return RegexExtractionStrategy(field_spec)

    elif strategy_type == StrategyType.NER:
        return NERExtractionStrategy(field_spec)

    elif strategy_type == StrategyType.LLM:
        return LLMExtractionStrategy(field_spec)

    else:
        raise InvalidStrategyConfigError(f"Unknown strategy type")


def _create_field_extractor(
    field_type: FieldType, strategy: ExtractionStrategy[List[str]]
) -> Union[FieldExtractor[str], FieldExtractor[List[str]]]:
    """Create field extractor (Name, Email, or Skills)."""
    if field_type == FieldType.NAME:
        return NameExtractor(strategy)
    elif field_type == FieldType.EMAIL:
        return EmailExtractor(strategy)
    elif field_type == FieldType.SKILLS:
        return SkillsExtractor(strategy)
    else:
        raise InvalidStrategyConfigError(f"Unknown field type: {field_type}")
