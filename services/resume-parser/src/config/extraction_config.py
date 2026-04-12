"""Configuration for extraction strategies.

This module defines the order of preferred extraction strategies for each field.
The framework will try strategies in order until one succeeds.
"""
#TODO: Add parsing config from file/database.

from typing import Dict, List
from dataclasses import dataclass
from interfaces import FieldType, StrategyType


@dataclass
class ExtractionConfig:
    """Configuration defining the preferred extraction strategies for each field.

    Each field can have multiple strategies listed in order of preference.
    The framework will try each strategy in sequence until one succeeds.

    Attributes:
        strategy_preferences: Dictionary mapping field types to ordered list of strategies
    """

    strategy_preferences: Dict[FieldType, List[StrategyType]]

    def get_strategies_for_field(self, field_type: FieldType) -> List[StrategyType]:
        """Get the ordered list of strategies for a specific field.

        Args:
            field_type: The field to get strategies for

        Returns:
            List of strategies in order of preference (empty if not configured)
        """
        return self.strategy_preferences.get(field_type, [])


# Default configuration: defines the preferred extraction strategies.
# Strategies are tried in order until one succeeds.
DEFAULT_EXTRACTION_CONFIG = ExtractionConfig(
    strategy_preferences={
        # Core identity — NER first (fastest for common patterns), LLM fallback
        FieldType.NAME: [StrategyType.NER, StrategyType.LLM],
        FieldType.EMAIL: [StrategyType.REGEX, StrategyType.NER, StrategyType.LLM],
        FieldType.SKILLS: [StrategyType.LLM, StrategyType.NER],

        # Contact info
        FieldType.PHONE: [StrategyType.REGEX, StrategyType.LLM],
        FieldType.LOCATION: [StrategyType.NER, StrategyType.LLM],
        FieldType.LINKEDIN_URL: [StrategyType.REGEX, StrategyType.LLM],
        FieldType.GITHUB_URL: [StrategyType.REGEX, StrategyType.LLM],
        FieldType.PORTFOLIO_URL: [StrategyType.LLM],
        FieldType.OTHER_URLS: [StrategyType.LLM],

        # Professional narrative — LLM only (semantic understanding required)
        FieldType.SUMMARY: [StrategyType.LLM],

        # Structured sections — LLM only (JSON object output)
        FieldType.WORK_EXPERIENCE: [StrategyType.LLM],
        FieldType.EDUCATION: [StrategyType.LLM],
        FieldType.CERTIFICATIONS: [StrategyType.LLM],
        FieldType.PROJECTS: [StrategyType.LLM],

        # Personal — LLM only
        FieldType.INTERESTS: [StrategyType.LLM],
        FieldType.LANGUAGES: [StrategyType.LLM],
        FieldType.AWARDS: [StrategyType.LLM],

        # Optional sections — LLM only
        FieldType.VOLUNTEER_EXPERIENCE: [StrategyType.LLM],
        FieldType.PUBLICATIONS: [StrategyType.LLM],
    }
)
