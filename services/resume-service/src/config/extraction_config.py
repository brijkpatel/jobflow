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
            List of strategies in order of preference
        """
        return self.strategy_preferences.get(field_type, [])


# Default configuration: defines the preferred extraction strategies
# Strategies are tried in order until one succeeds
DEFAULT_EXTRACTION_CONFIG = ExtractionConfig(
    strategy_preferences={
        # For NAME: Try NER first (best accuracy), then fallback to LLM
        FieldType.NAME: [
            StrategyType.NER,
            StrategyType.LLM,
        ],
        # For EMAIL: Try Regex first (fastest), then NER, then LLM
        FieldType.EMAIL: [
            StrategyType.REGEX,
            StrategyType.NER,
            StrategyType.LLM,
        ],
        # For SKILLS: Try LLM first (best for skills), then fallback to NER
        FieldType.SKILLS: [
            StrategyType.LLM,
            StrategyType.NER,
        ],
    }
)
