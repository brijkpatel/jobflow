"""Unit tests for LLMExtractionStrategy."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from interfaces.extracting_strategy import FieldSpec, FieldType
from extractors.strategies.llm import LLMExtractionStrategy
from exceptions import (
    InvalidStrategyConfigError,
    NoMatchFoundError,
    ExternalServiceError,
)


class TestLLMExtractionStrategy:
    """Tests for LLMExtractionStrategy."""

    @patch("extractors.strategies.llm.genai.GenerativeModel")
    def test_init_success(self, mock_model_class: MagicMock):
        """Test successful initialization."""
        mock_model = Mock()
        mock_model_class.return_value = mock_model
        spec = FieldSpec(field_type=FieldType.NAME)

        strategy = LLMExtractionStrategy(spec)

        assert strategy.model == mock_model
        assert strategy.spec == spec
        mock_model_class.assert_called_once_with("gemini-2.0-flash-exp")

    @patch("extractors.strategies.llm.genai.GenerativeModel")
    def test_init_with_custom_model(self, mock_model_class: MagicMock):
        """Test initialization with custom model name."""
        mock_model = Mock()
        mock_model_class.return_value = mock_model
        spec = FieldSpec(field_type=FieldType.NAME)

        strategy = LLMExtractionStrategy(spec, model_name="gemini-pro")

        assert strategy.model == mock_model
        assert strategy.spec == spec
        mock_model_class.assert_called_once_with("gemini-pro")

    @patch("extractors.strategies.llm.genai.GenerativeModel")
    def test_init_model_failure(self, mock_model_class: MagicMock):
        """Test model initialization failure raises error."""
        mock_model_class.side_effect = Exception("Model init failed")
        spec = FieldSpec(field_type=FieldType.NAME)

        with pytest.raises(InvalidStrategyConfigError):
            LLMExtractionStrategy(spec)

    @patch("extractors.strategies.llm.genai.GenerativeModel")
    def test_extract_single_value(self, mock_model_class: MagicMock):
        """Test extracting single value."""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "John Doe"
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        spec = FieldSpec(field_type=FieldType.NAME)

        strategy = LLMExtractionStrategy(spec)

        result = strategy.extract("My name is John Doe")

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == "John Doe"

    @patch("extractors.strategies.llm.genai.GenerativeModel")
    def test_extract_multi_value_json(self, mock_model_class: MagicMock):
        """Test extracting multiple values from JSON response."""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = '["Python", "Java", "JavaScript"]'
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        spec = FieldSpec(field_type=FieldType.SKILLS, top_k=2)

        strategy = LLMExtractionStrategy(spec)

        result = strategy.extract("Skills: Python, Java, JavaScript")

        assert isinstance(result, list)
        assert len(result) == 2
        assert result == ["Python", "Java"]

    @patch("extractors.strategies.llm.genai.GenerativeModel")
    def test_extract_multi_value_with_extra_text(self, mock_model_class: MagicMock):
        """Test extracting JSON array embedded in response text."""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = 'Here are the skills: ["Python", "Java"] from the text.'
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        spec = FieldSpec(field_type=FieldType.SKILLS, top_k=0)

        strategy = LLMExtractionStrategy(spec)

        result = strategy.extract("Some text")

        assert result == ["Python", "Java"]

    @patch("extractors.strategies.llm.genai.GenerativeModel")
    def test_extract_empty_text_raises_error(self, mock_model_class: MagicMock):
        """Test empty text raises error."""
        mock_model_class.return_value = Mock()
        spec = FieldSpec(field_type=FieldType.NAME)

        strategy = LLMExtractionStrategy(spec)

        with pytest.raises(NoMatchFoundError, match="Cannot extract from empty text"):
            strategy.extract("   ")

    @patch("extractors.strategies.llm.genai.GenerativeModel")
    def test_extract_not_found_response(self, mock_model_class: MagicMock):
        """Test NOT_FOUND response raises error."""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "NOT_FOUND"
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        spec = FieldSpec(field_type=FieldType.NAME)

        strategy = LLMExtractionStrategy(spec)

        with pytest.raises(NoMatchFoundError, match="LLM could not find field"):
            strategy.extract("Some text")

    @patch("extractors.strategies.llm.genai.GenerativeModel")
    def test_extract_empty_response(self, mock_model_class: MagicMock):
        """Test empty LLM response raises error."""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = ""
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        spec = FieldSpec(field_type=FieldType.NAME)

        strategy = LLMExtractionStrategy(spec)

        with pytest.raises(NoMatchFoundError, match="LLM returned empty response"):
            strategy.extract("Some text")

    @patch("extractors.strategies.llm.genai.GenerativeModel")
    def test_extract_invalid_json_raises_error(self, mock_model_class: MagicMock):
        """Test invalid JSON response raises error."""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = '["Python", "Java"'  # Invalid JSON
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        spec = FieldSpec(field_type=FieldType.SKILLS, top_k=0)

        strategy = LLMExtractionStrategy(spec)

        with pytest.raises(ExternalServiceError):
            strategy.extract("Some text")

    @patch("extractors.strategies.llm.genai.GenerativeModel")
    def test_extract_api_failure(self, mock_model_class: MagicMock):
        """Test API failure raises ExternalServiceError."""
        mock_model = Mock()
        mock_model.generate_content.side_effect = Exception("API Error")
        mock_model_class.return_value = mock_model
        spec = FieldSpec(field_type=FieldType.NAME)

        strategy = LLMExtractionStrategy(spec)

        with pytest.raises(ExternalServiceError):
            strategy.extract("Some text")

    @patch("extractors.strategies.llm.genai.GenerativeModel")
    def test_extract_empty_json_array(self, mock_model_class: MagicMock):
        """Test empty JSON array raises NoMatchFoundError."""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "[]"
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        spec = FieldSpec(field_type=FieldType.SKILLS, top_k=0)

        strategy = LLMExtractionStrategy(spec)

        with pytest.raises(NoMatchFoundError, match="LLM found no values"):
            strategy.extract("Some text")

    @patch("extractors.strategies.llm.genai.GenerativeModel")
    def test_extract_non_list_json_response(self, mock_model_class: MagicMock):
        """Test non-list JSON response raises error."""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = '{"key": "value"}'  # Object instead of array
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        spec = FieldSpec(field_type=FieldType.SKILLS, top_k=0)

        strategy = LLMExtractionStrategy(spec)

        with pytest.raises(ExternalServiceError):
            strategy.extract("Some text")

    @patch("extractors.strategies.llm.genai.GenerativeModel")
    def test_build_prompt_for_different_field_types(self, mock_model_class: MagicMock):
        """Test prompt building for different field types."""
        mock_model = Mock()
        mock_model_class.return_value = mock_model
        spec_name = FieldSpec(field_type=FieldType.NAME)
        spec_skills = FieldSpec(field_type=FieldType.SKILLS, top_k=5)

        strategy_name = LLMExtractionStrategy(spec_name)
        strategy_skills = LLMExtractionStrategy(spec_skills)

        # Test NAME field
        prompt_name = strategy_name._build_prompt("text", spec_name)
        assert "full name" in prompt_name.lower()
        assert "JSON array" in prompt_name

        # Test SKILLS field with top_k
        prompt_skills = strategy_skills._build_prompt("text", spec_skills)
        assert "skills" in prompt_skills.lower()
        assert "JSON array" in prompt_skills
