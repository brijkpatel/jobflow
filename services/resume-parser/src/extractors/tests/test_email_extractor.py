"""Tests for EmailExtractor."""

import pytest
from unittest.mock import Mock

from extractors.email_extractor import EmailExtractor
from interfaces import ExtractionStrategy
from exceptions import FieldExtractionError


class TestEmailExtractor:
    """Test cases for EmailExtractor."""

    def test_extract_success(self):
        """Test successful email extraction."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["john.doe@example.com"]
        extractor = EmailExtractor(mock_strategy)
        text = "Contact me at john.doe@example.com"

        # Act
        result = extractor.extract(text)

        # Assert
        assert result == "john.doe@example.com"
        mock_strategy.extract.assert_called_once_with(text)

    def test_extract_returns_first_email(self):
        """Test that extractor returns the first email when multiple are found."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = [
            "first@example.com",
            "second@example.com",
        ]
        extractor = EmailExtractor(mock_strategy)

        # Act
        result = extractor.extract("Multiple emails here")

        # Assert
        assert result == "first@example.com"

    def test_extract_no_emails_found(self):
        """Test extraction when no emails are found."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = []
        extractor = EmailExtractor(mock_strategy)

        # Act & Assert
        with pytest.raises(FieldExtractionError, match="Email extraction failed"):
            extractor.extract("Some text without emails")

    def test_extract_with_whitespace(self):
        """Test extraction with leading/trailing whitespace."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["valid@email.com"]
        extractor = EmailExtractor(mock_strategy)

        # Act
        result = extractor.extract("   Resume text with email   ")

        # Assert
        assert result == "valid@email.com"
        mock_strategy.extract.assert_called_once_with("Resume text with email")

    def test_extract_strategy_raises_exception(self):
        """Test when strategy raises an exception."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.side_effect = ValueError("Strategy failed")
        extractor = EmailExtractor(mock_strategy)

        # Act & Assert
        with pytest.raises(FieldExtractionError, match="Email extraction failed"):
            extractor.extract("Some text with enough characters")

    def test_validate_input_empty_string(self):
        """Test validation with empty string."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)
        extractor = EmailExtractor(mock_strategy)

        # Act & Assert
        with pytest.raises(
            FieldExtractionError,
            match="Input text must be at least 5 characters long after stripping",
        ):
            extractor.extract("")

    def test_validate_input_too_short(self):
        """Test validation with string shorter than 5 characters."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)
        extractor = EmailExtractor(mock_strategy)

        # Act & Assert
        with pytest.raises(
            FieldExtractionError,
            match="Input text must be at least 5 characters long after stripping",
        ):
            extractor.extract("abc")

    def test_validate_input_whitespace_only(self):
        """Test validation with whitespace-only string."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)
        extractor = EmailExtractor(mock_strategy)

        # Act & Assert
        with pytest.raises(
            FieldExtractionError,
            match="Input text must be at least 5 characters long after stripping",
        ):
            extractor.extract("     ")

    def test_validate_input_exactly_five_characters(self):
        """Test validation with exactly 5 characters (edge case - should pass if valid email)."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)
        # Note: "a@b.c" is actually an invalid email format (TLD must be at least 2 chars)
        # So this test should expect a validation error
        mock_strategy.extract.return_value = ["a@b.c"]
        extractor = EmailExtractor(mock_strategy)

        # Act & Assert - This should fail validation
        with pytest.raises(FieldExtractionError, match="Email extraction failed"):
            extractor.extract("a@b.c")

    def test_validate_email_format_valid(self):
        """Test email format validation with valid email."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["valid.email@example.com"]
        extractor = EmailExtractor(mock_strategy)

        # Act
        result = extractor.extract("Contact: valid.email@example.com")

        # Assert
        assert result == "valid.email@example.com"

    def test_validate_email_format_invalid_no_at(self):
        """Test email format validation with invalid email (no @)."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["invalidemail.com"]
        extractor = EmailExtractor(mock_strategy)

        # Act & Assert
        with pytest.raises(FieldExtractionError, match="Email extraction failed"):
            extractor.extract("Contact: invalidemail.com")

    def test_validate_email_format_invalid_no_domain(self):
        """Test email format validation with invalid email (no domain)."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["user@"]
        extractor = EmailExtractor(mock_strategy)

        # Act & Assert
        with pytest.raises(FieldExtractionError, match="Email extraction failed"):
            extractor.extract("Contact: user@")

    def test_validate_email_format_invalid_no_tld(self):
        """Test email format validation with invalid email (no TLD)."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["user@domain"]
        extractor = EmailExtractor(mock_strategy)

        # Act & Assert
        with pytest.raises(FieldExtractionError, match="Email extraction failed"):
            extractor.extract("Contact: user@domain")

    def test_validate_email_format_with_plus_sign(self):
        """Test email format validation with plus sign (valid)."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["user+tag@example.com"]
        extractor = EmailExtractor(mock_strategy)

        # Act
        result = extractor.extract("Contact: user+tag@example.com")

        # Assert
        assert result == "user+tag@example.com"

    def test_validate_email_format_with_subdomain(self):
        """Test email format validation with subdomain (valid)."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["user@mail.example.com"]
        extractor = EmailExtractor(mock_strategy)

        # Act
        result = extractor.extract("Contact: user@mail.example.com")

        # Assert
        assert result == "user@mail.example.com"

    def test_validate_email_format_with_numbers(self):
        """Test email format validation with numbers (valid)."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["user123@example456.com"]
        extractor = EmailExtractor(mock_strategy)

        # Act
        result = extractor.extract("Contact: user123@example456.com")

        # Assert
        assert result == "user123@example456.com"

    def test_extractor_initialization(self):
        """Test that extractor initializes correctly."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)

        # Act
        extractor = EmailExtractor(mock_strategy)

        # Assert
        assert extractor.extraction_strategy == mock_strategy
