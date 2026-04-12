"""Tests for extractor factory."""

import pytest
from unittest.mock import patch, Mock

from extractors.factory import (
    create_extractor,
    _create_field_spec,
    _create_strategy,
    _create_field_extractor,
    SUPPORTED_STRATEGIES,
)
from extractors.name_extractor import NameExtractor
from extractors.email_extractor import EmailExtractor
from extractors.skills_extractor import SkillsExtractor
from extractors.strategies.regex import RegexExtractionStrategy
from extractors.strategies.ner import NERExtractionStrategy
from extractors.strategies.llm import LLMExtractionStrategy
from interfaces import FieldType, StrategyType, FieldSpec, ExtractionStrategy
from exceptions import InvalidStrategyConfigError


class TestCreateExtractor:
    """Test cases for create_extractor function."""

    @patch("extractors.factory.NERExtractionStrategy")
    def test_create_name_extractor_with_ner(self, mock_ner_class):
        """Test creating name extractor with NER strategy."""
        # Arrange
        mock_strategy = mock_ner_class.return_value

        # Act
        extractor = create_extractor(FieldType.NAME, StrategyType.NER)

        # Assert
        assert isinstance(extractor, NameExtractor)
        mock_ner_class.assert_called_once()
        # Verify the FieldSpec passed to strategy
        call_args = mock_ner_class.call_args
        field_spec = call_args[0][0]
        assert field_spec.field_type == FieldType.NAME
        assert field_spec.entity_label == "person"
        assert field_spec.top_k is None

    @patch("extractors.factory.LLMExtractionStrategy")
    def test_create_name_extractor_with_llm(self, mock_llm_class):
        """Test creating name extractor with LLM strategy."""
        # Arrange
        mock_strategy = mock_llm_class.return_value

        # Act
        extractor = create_extractor(FieldType.NAME, StrategyType.LLM)

        # Assert
        assert isinstance(extractor, NameExtractor)
        mock_llm_class.assert_called_once()

    def test_create_name_extractor_with_regex_fails(self):
        """Test that creating name extractor with regex strategy fails."""
        # Act & Assert
        with pytest.raises(
            InvalidStrategyConfigError,
            match="Strategy is not supported for field",
        ):
            create_extractor(FieldType.NAME, StrategyType.REGEX)

    @patch("extractors.factory.RegexExtractionStrategy")
    def test_create_email_extractor_with_regex(self, mock_regex_class):
        """Test creating email extractor with regex strategy."""
        # Arrange
        mock_strategy = mock_regex_class.return_value

        # Act
        extractor = create_extractor(FieldType.EMAIL, StrategyType.REGEX)

        # Assert
        assert isinstance(extractor, EmailExtractor)
        mock_regex_class.assert_called_once()
        # Verify the FieldSpec is passed with regex patterns
        call_args = mock_regex_class.call_args
        field_spec = call_args[0][0]
        assert field_spec.field_type == FieldType.EMAIL
        assert field_spec.regex_patterns is not None

    @patch("extractors.factory.NERExtractionStrategy")
    def test_create_email_extractor_with_ner(self, mock_ner_class):
        """Test creating email extractor with NER strategy."""
        # Arrange
        mock_strategy = mock_ner_class.return_value

        # Act
        extractor = create_extractor(FieldType.EMAIL, StrategyType.NER)

        # Assert
        assert isinstance(extractor, EmailExtractor)
        mock_ner_class.assert_called_once()

    @patch("extractors.factory.LLMExtractionStrategy")
    def test_create_email_extractor_with_llm(self, mock_llm_class):
        """Test creating email extractor with LLM strategy."""
        # Arrange
        mock_strategy = mock_llm_class.return_value

        # Act
        extractor = create_extractor(FieldType.EMAIL, StrategyType.LLM)

        # Assert
        assert isinstance(extractor, EmailExtractor)
        mock_llm_class.assert_called_once()

    @patch("extractors.factory.NERExtractionStrategy")
    def test_create_skills_extractor_with_ner(self, mock_ner_class):
        """Test creating skills extractor with NER strategy."""
        # Arrange
        mock_strategy = mock_ner_class.return_value

        # Act
        extractor = create_extractor(FieldType.SKILLS, StrategyType.NER)

        # Assert
        assert isinstance(extractor, SkillsExtractor)
        mock_ner_class.assert_called_once()
        # Verify the FieldSpec for multi-valued field
        call_args = mock_ner_class.call_args
        field_spec = call_args[0][0]
        assert field_spec.field_type == FieldType.SKILLS
        assert field_spec.entity_label == "skill"
        assert field_spec.top_k == 0  # No limit

    @patch("extractors.factory.LLMExtractionStrategy")
    def test_create_skills_extractor_with_llm(self, mock_llm_class):
        """Test creating skills extractor with LLM strategy."""
        # Arrange
        mock_strategy = mock_llm_class.return_value

        # Act
        extractor = create_extractor(FieldType.SKILLS, StrategyType.LLM)

        # Assert
        assert isinstance(extractor, SkillsExtractor)
        mock_llm_class.assert_called_once()

    def test_create_skills_extractor_with_regex_fails(self):
        """Test that creating skills extractor with regex strategy fails."""
        # Act & Assert
        with pytest.raises(
            InvalidStrategyConfigError,
            match="Strategy is not supported for field",
        ):
            create_extractor(FieldType.SKILLS, StrategyType.REGEX)


class TestCreateFieldSpec:
    """Test cases for _create_field_spec function."""

    def test_create_field_spec_for_name(self):
        """Test creating FieldSpec for NAME field."""
        # Act
        spec = _create_field_spec(FieldType.NAME)

        # Assert
        assert spec.field_type == FieldType.NAME
        assert spec.entity_label == "person"
        assert spec.top_k is None  # Single-valued
        assert spec.regex_patterns is None

    def test_create_field_spec_for_email(self):
        """Test creating FieldSpec for EMAIL field."""
        # Act
        spec = _create_field_spec(FieldType.EMAIL)

        # Assert
        assert spec.field_type == FieldType.EMAIL
        assert spec.entity_label == "email"
        assert spec.top_k is None  # Single-valued
        assert spec.regex_patterns is not None
        assert len(spec.regex_patterns) > 0

    def test_create_field_spec_for_skills(self):
        """Test creating FieldSpec for SKILLS field."""
        # Act
        spec = _create_field_spec(FieldType.SKILLS)

        # Assert
        assert spec.field_type == FieldType.SKILLS
        assert spec.entity_label == "skill"
        assert spec.top_k == 0  # Multi-valued, no limit
        assert spec.regex_patterns is None


class TestCreateStrategy:
    """Test cases for _create_strategy function."""

    def test_create_regex_strategy(self):
        """Test creating regex strategy."""
        # Arrange
        spec = FieldSpec(
            field_type=FieldType.EMAIL,
            regex_patterns=["test_pattern"],
            top_k=None,
        )

        # Act
        strategy = _create_strategy(FieldType.EMAIL, StrategyType.REGEX, spec)

        # Assert
        assert isinstance(strategy, RegexExtractionStrategy)

    def test_create_regex_strategy_without_patterns_fails(self):
        """Test creating regex strategy without patterns fails."""
        # Arrange
        spec = FieldSpec(field_type=FieldType.NAME, top_k=None)

        # Act & Assert
        with pytest.raises(
            InvalidStrategyConfigError,
            match="Regex patterns not configured for field",
        ):
            _create_strategy(FieldType.NAME, StrategyType.REGEX, spec)

    @patch("extractors.factory.NERExtractionStrategy")
    def test_create_ner_strategy(self, mock_ner_class):
        """Test creating NER strategy."""
        # Arrange
        spec = FieldSpec(field_type=FieldType.NAME, entity_label="person", top_k=None)

        # Act
        strategy = _create_strategy(FieldType.NAME, StrategyType.NER, spec)

        # Assert
        mock_ner_class.assert_called_once_with(spec)

    @patch("extractors.factory.LLMExtractionStrategy")
    def test_create_llm_strategy(self, mock_llm_class):
        """Test creating LLM strategy."""
        # Arrange
        spec = FieldSpec(field_type=FieldType.NAME, top_k=None)

        # Act
        strategy = _create_strategy(FieldType.NAME, StrategyType.LLM, spec)

        # Assert
        mock_llm_class.assert_called_once_with(spec)

    def test_create_strategy_unknown_type(self):
        """Test creating strategy with unknown type (hypothetical)."""
        # This test checks edge case if StrategyType enum is extended
        # For now, we'll skip this as all enum values are handled
        pass


class TestCreateFieldExtractor:
    """Test cases for _create_field_extractor function."""

    def test_create_name_extractor(self):
        """Test creating NameExtractor."""
        # Arrange
        strategy = Mock(spec=ExtractionStrategy)

        # Act
        extractor = _create_field_extractor(FieldType.NAME, strategy)

        # Assert
        assert isinstance(extractor, NameExtractor)
        assert extractor.extraction_strategy == strategy

    def test_create_email_extractor(self):
        """Test creating EmailExtractor."""
        # Arrange
        strategy = Mock(spec=ExtractionStrategy)

        # Act
        extractor = _create_field_extractor(FieldType.EMAIL, strategy)

        # Assert
        assert isinstance(extractor, EmailExtractor)
        assert extractor.extraction_strategy == strategy

    def test_create_skills_extractor(self):
        """Test creating SkillsExtractor."""
        # Arrange
        strategy = Mock(spec=ExtractionStrategy)

        # Act
        extractor = _create_field_extractor(FieldType.SKILLS, strategy)

        # Assert
        assert isinstance(extractor, SkillsExtractor)
        assert extractor.extraction_strategy == strategy


class TestSupportedStrategies:
    """Test cases for supported strategies configuration."""

    def test_name_supported_strategies(self):
        """Test NAME field supported strategies."""
        strategies = SUPPORTED_STRATEGIES[FieldType.NAME]
        assert StrategyType.NER in strategies
        assert StrategyType.LLM in strategies
        assert StrategyType.REGEX not in strategies

    def test_email_supported_strategies(self):
        """Test EMAIL field supported strategies."""
        strategies = SUPPORTED_STRATEGIES[FieldType.EMAIL]
        assert StrategyType.REGEX in strategies
        assert StrategyType.NER in strategies
        assert StrategyType.LLM in strategies

    def test_skills_supported_strategies(self):
        """Test SKILLS field supported strategies."""
        strategies = SUPPORTED_STRATEGIES[FieldType.SKILLS]
        assert StrategyType.NER in strategies
        assert StrategyType.LLM in strategies
        assert StrategyType.REGEX not in strategies


class TestFactoryIntegration:
    """Integration tests for factory end-to-end."""

    @patch("extractors.factory.NERExtractionStrategy")
    def test_end_to_end_name_extraction_ner(self, mock_ner_class):
        """Test end-to-end name extraction with NER."""
        # Arrange
        mock_strategy = mock_ner_class.return_value
        mock_strategy.extract.return_value = ["John Doe"]

        # Act
        extractor = create_extractor(FieldType.NAME, StrategyType.NER)
        result = extractor.extract("Resume text with John Doe")

        # Assert
        assert result == "John Doe"
        mock_strategy.extract.assert_called_once()

    @patch("extractors.factory.RegexExtractionStrategy")
    def test_end_to_end_email_extraction_regex(self, mock_regex_class):
        """Test end-to-end email extraction with regex."""
        # Arrange
        mock_strategy = mock_regex_class.return_value
        mock_strategy.extract.return_value = ["test@example.com"]

        # Act
        extractor = create_extractor(FieldType.EMAIL, StrategyType.REGEX)
        result = extractor.extract("Contact: test@example.com")

        # Assert
        assert result == "test@example.com"
        mock_strategy.extract.assert_called_once()

    @patch("extractors.factory.LLMExtractionStrategy")
    def test_end_to_end_skills_extraction_llm(self, mock_llm_class):
        """Test end-to-end skills extraction with LLM."""
        # Arrange
        mock_strategy = mock_llm_class.return_value
        mock_strategy.extract.return_value = ["Python", "Java", "SQL"]

        # Act
        extractor = create_extractor(FieldType.SKILLS, StrategyType.LLM)
        result = extractor.extract("Skills: Python, Java, SQL")

        # Assert
        assert result == ["Python", "Java", "SQL"]
        mock_strategy.extract.assert_called_once()

    def test_multiple_extractors_different_strategies(self):
        """Test creating multiple extractors with different strategies."""
        # This test verifies that factory can create multiple extractors
        # and they don't interfere with each other
        with patch("extractors.factory.RegexExtractionStrategy") as mock_regex, patch(
            "extractors.factory.NERExtractionStrategy"
        ) as mock_ner, patch("extractors.factory.LLMExtractionStrategy") as mock_llm:

            # Act
            email_extractor = create_extractor(FieldType.EMAIL, StrategyType.REGEX)
            name_extractor = create_extractor(FieldType.NAME, StrategyType.NER)
            skills_extractor = create_extractor(FieldType.SKILLS, StrategyType.LLM)

            # Assert
            assert isinstance(email_extractor, EmailExtractor)
            assert isinstance(name_extractor, NameExtractor)
            assert isinstance(skills_extractor, SkillsExtractor)
            mock_regex.assert_called_once()
            mock_ner.assert_called_once()
            mock_llm.assert_called_once()
