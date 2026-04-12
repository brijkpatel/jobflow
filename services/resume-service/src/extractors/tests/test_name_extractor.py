"""Tests for NameExtractor."""

import pytest
from unittest.mock import Mock

from extractors.name_extractor import NameExtractor
from interfaces import ExtractionStrategy
from exceptions import FieldExtractionError


class TestNameExtractor:
    """Test cases for NameExtractor."""

    def test_extract_success(self):
        """Test successful name extraction."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["John Doe", "Jane Smith"]
        extractor = NameExtractor(mock_strategy)
        text = "John Doe is a software engineer."

        # Act
        result = extractor.extract(text)

        # Assert
        assert result == "John Doe"
        mock_strategy.extract.assert_called_once_with(text)

    def test_extract_returns_first_name(self):
        """Test that extractor returns the first name when multiple are found."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["Alice Johnson", "Bob Williams"]
        extractor = NameExtractor(mock_strategy)

        # Act
        result = extractor.extract("Some resume text")

        # Assert
        assert result == "Alice Johnson"

    def test_extract_no_names_found(self):
        """Test extraction when no names are found."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = []
        extractor = NameExtractor(mock_strategy)

        # Act & Assert
        with pytest.raises(FieldExtractionError, match="Name extraction failed"):
            extractor.extract("Some text without names")

    def test_extract_with_whitespace(self):
        """Test extraction with leading/trailing whitespace."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["Sarah Connor"]
        extractor = NameExtractor(mock_strategy)

        # Act
        result = extractor.extract("   Resume text with spaces   ")

        # Assert
        assert result == "Sarah Connor"
        mock_strategy.extract.assert_called_once_with("Resume text with spaces")

    def test_extract_strategy_raises_exception(self):
        """Test when strategy raises an exception."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.side_effect = ValueError("Strategy failed")
        extractor = NameExtractor(mock_strategy)

        # Act & Assert
        with pytest.raises(FieldExtractionError, match="Name extraction failed"):
            extractor.extract("Some text")

    def test_validate_input_empty_string(self):
        """Test validation with empty string."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)
        extractor = NameExtractor(mock_strategy)

        # Act & Assert
        with pytest.raises(
            FieldExtractionError,
            match="Input text must be at least 1 character long after stripping",
        ):
            extractor.extract("")

    def test_validate_input_whitespace_only(self):
        """Test validation with whitespace-only string."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)
        extractor = NameExtractor(mock_strategy)

        # Act & Assert
        with pytest.raises(
            FieldExtractionError,
            match="Input text must be at least 1 character long after stripping",
        ):
            extractor.extract("   ")

    def test_validate_input_single_character(self):
        """Test validation with single character (edge case - should pass)."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["A"]
        extractor = NameExtractor(mock_strategy)

        # Act
        result = extractor.extract("A")

        # Assert
        assert result == "A"

    def test_extract_with_none_in_list(self):
        """Test extraction when strategy returns None values."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = [None, "Valid Name"]
        extractor = NameExtractor(mock_strategy)

        # Act
        result = extractor.extract("Some text")

        # Assert
        # Should return the first item (even if None) - the strategy should handle filtering
        assert result is None

    def test_extractor_initialization(self):
        """Test that extractor initializes correctly."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)

        # Act
        extractor = NameExtractor(mock_strategy)

        # Assert
        assert extractor.extraction_strategy == mock_strategy
