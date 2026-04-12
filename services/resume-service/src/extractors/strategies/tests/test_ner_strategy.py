"""Unit tests for NERExtractionStrategy."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from interfaces import FieldSpec, FieldType
from ..ner import NERExtractionStrategy
from exceptions import (
    InvalidStrategyConfigError,
    NoMatchFoundError,
    StrategyExtractionError,
)


class TestNERExtractionStrategy:
    """Tests for NERExtractionStrategy."""

    @patch("extractors.strategies.ner.GLiNER.from_pretrained")
    def test_init_with_invalid_model(self, mock_gliner: MagicMock):
        """Test initialization with non-existent model raises error."""
        mock_gliner.side_effect = Exception("Model not found")
        spec = FieldSpec(field_type=FieldType.NAME)
        with pytest.raises(InvalidStrategyConfigError):
            NERExtractionStrategy(spec, model_name="invalid_model_xyz")

    @patch("extractors.strategies.ner.GLiNER.from_pretrained")
    def test_init_with_valid_model(self, mock_gliner: MagicMock):
        """Test successful initialization."""
        mock_model = Mock()
        mock_gliner.return_value = mock_model
        spec = FieldSpec(field_type=FieldType.NAME)

        strategy = NERExtractionStrategy(spec)
        assert strategy.model == mock_model
        assert strategy.spec == spec
        mock_gliner.assert_called_once_with("urchade/gliner_multi_pii-v1")

    @patch("extractors.strategies.ner.GLiNER.from_pretrained")
    def test_extract_single_entity(self, mock_gliner: MagicMock):
        """Test extracting single entity."""
        mock_model = Mock()
        mock_model.predict_entities.return_value = [
            {"text": "John Doe", "label": "person", "score": 0.95}
        ]
        mock_gliner.return_value = mock_model
        spec = FieldSpec(field_type=FieldType.NAME)

        strategy = NERExtractionStrategy(spec, default_entity_label="person")

        result = strategy.extract("My name is John Doe")
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == "John Doe"
        mock_model.predict_entities.assert_called_once_with(
            "My name is John Doe", ["person"]
        )

    @patch("extractors.strategies.ner.GLiNER.from_pretrained")
    def test_extract_multiple_entities_with_top_k(self, mock_gliner: MagicMock):
        """Test extracting multiple entities with limit."""
        mock_model = Mock()
        mock_model.predict_entities.return_value = [
            {"text": "Python", "label": "skill", "score": 0.95},
            {"text": "Java", "label": "skill", "score": 0.93},
            {"text": "JavaScript", "label": "skill", "score": 0.91},
            {"text": "Ruby", "label": "skill", "score": 0.89},
        ]
        mock_gliner.return_value = mock_model
        spec = FieldSpec(field_type=FieldType.SKILLS, entity_label="skill", top_k=2)

        strategy = NERExtractionStrategy(spec)

        result = strategy.extract("I know Python Java JavaScript Ruby")
        assert isinstance(result, list)
        assert len(result) == 2
        assert result == ["Python", "Java"]

    @patch("extractors.strategies.ner.GLiNER.from_pretrained")
    def test_extract_no_entity_label_raises_error(self, mock_gliner: MagicMock):
        """Test missing entity_label raises error."""
        mock_model = Mock()
        mock_gliner.return_value = mock_model
        spec = FieldSpec(field_type=FieldType.NAME)

        strategy = NERExtractionStrategy(spec)

        with pytest.raises(
            InvalidStrategyConfigError, match="entity_label must be provided"
        ):
            strategy.extract("Some text")

    @patch("extractors.strategies.ner.GLiNER.from_pretrained")
    def test_extract_empty_text_raises_error(self, mock_gliner: MagicMock):
        """Test empty text raises error."""
        mock_model = Mock()
        mock_gliner.return_value = mock_model
        spec = FieldSpec(field_type=FieldType.NAME)

        strategy = NERExtractionStrategy(spec, default_entity_label="person")

        with pytest.raises(NoMatchFoundError, match="Cannot extract from empty text"):
            strategy.extract("")

    @patch("extractors.strategies.ner.GLiNER.from_pretrained")
    def test_extract_no_entities_found_raises_error(self, mock_gliner: MagicMock):
        """Test no matching entities raises error."""
        mock_model = Mock()
        mock_model.predict_entities.return_value = []
        mock_gliner.return_value = mock_model
        spec = FieldSpec(field_type=FieldType.NAME)

        strategy = NERExtractionStrategy(spec, default_entity_label="person")

        with pytest.raises(NoMatchFoundError, match="No entities found"):
            strategy.extract("Some text without entities")

    @patch("extractors.strategies.ner.GLiNER.from_pretrained")
    def test_extract_gliner_processing_error(self, mock_gliner: MagicMock):
        """Test GLiNER processing failure raises error."""
        mock_model = Mock()
        mock_model.predict_entities.side_effect = Exception("Processing failed")
        mock_gliner.return_value = mock_model
        spec = FieldSpec(field_type=FieldType.NAME)

        strategy = NERExtractionStrategy(spec, default_entity_label="person")

        with pytest.raises(StrategyExtractionError):
            strategy.extract("Some text")

    @patch("extractors.strategies.ner.GLiNER.from_pretrained")
    def test_extract_with_top_k_zero_returns_all(self, mock_gliner: MagicMock):
        """Test top_k=0 returns all entities."""
        mock_model = Mock()
        mock_model.predict_entities.return_value = [
            {"text": "Alice", "label": "person", "score": 0.95},
            {"text": "Bob", "label": "person", "score": 0.93},
            {"text": "Charlie", "label": "person", "score": 0.91},
        ]
        mock_gliner.return_value = mock_model
        spec = FieldSpec(field_type=FieldType.NAME, top_k=0)

        strategy = NERExtractionStrategy(spec, default_entity_label="person")

        result = strategy.extract("Alice Bob Charlie")
        assert len(result) == 3
        assert result == ["Alice", "Bob", "Charlie"]
