"""Tests for PhoneExtractor."""

import pytest
from unittest.mock import Mock

from extractors.phone_extractor import PhoneExtractor
from interfaces import ExtractionStrategy
from exceptions import FieldExtractionError


class TestPhoneExtractorExtract:
    """Tests for PhoneExtractor.extract()."""

    def test_extract_success(self):
        """Test successful phone extraction."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["+1-800-555-1234"]
        extractor = PhoneExtractor(mock_strategy)

        result = extractor.extract("Call me at +1-800-555-1234")

        assert result == "+1-800-555-1234"
        mock_strategy.extract.assert_called_once()

    def test_extract_returns_first_result(self):
        """Test that only the first number is returned when multiple are found."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["555-1234", "555-9876"]
        extractor = PhoneExtractor(mock_strategy)

        result = extractor.extract("Phones: 555-1234, 555-9876")

        assert result == "555-1234"

    def test_extract_strips_whitespace_from_result(self):
        """Test that leading/trailing whitespace in result is stripped."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["  555-1234567  "]
        extractor = PhoneExtractor(mock_strategy)

        result = extractor.extract("Phone: 555-1234567")

        assert result == "555-1234567"

    def test_extract_empty_text_raises_error(self):
        """Test that empty input text raises FieldExtractionError."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        extractor = PhoneExtractor(mock_strategy)

        with pytest.raises(FieldExtractionError, match="Input text is empty"):
            extractor.extract("")

    def test_extract_whitespace_only_text_raises_error(self):
        """Test that whitespace-only input raises FieldExtractionError."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        extractor = PhoneExtractor(mock_strategy)

        with pytest.raises(FieldExtractionError, match="Input text is empty"):
            extractor.extract("   ")

    def test_extract_no_phone_found_raises_error(self):
        """Test that empty results list raises FieldExtractionError."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = []
        extractor = PhoneExtractor(mock_strategy)

        with pytest.raises(FieldExtractionError, match="No phone number found"):
            extractor.extract("Some resume text without a phone")

    def test_extract_too_few_digits_raises_error(self):
        """Test that a result with fewer than 7 digits raises FieldExtractionError."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["123"]
        extractor = PhoneExtractor(mock_strategy)

        with pytest.raises(FieldExtractionError, match="does not look like a phone number"):
            extractor.extract("Phone: 123")

    def test_extract_exactly_seven_digits_succeeds(self):
        """Test that exactly 7 digits passes validation."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["555-1234"]
        extractor = PhoneExtractor(mock_strategy)

        result = extractor.extract("Phone: 555-1234")

        assert result == "555-1234"

    def test_extract_strategy_exception_wrapped_in_field_error(self):
        """Test that strategy exceptions are wrapped in FieldExtractionError."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.side_effect = RuntimeError("network error")
        extractor = PhoneExtractor(mock_strategy)

        with pytest.raises(FieldExtractionError, match="Phone extraction failed"):
            extractor.extract("Resume text here")

    def test_extract_international_format(self):
        """Test extraction of international phone format."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["+44 20 7946 0958"]
        extractor = PhoneExtractor(mock_strategy)

        result = extractor.extract("UK phone: +44 20 7946 0958")

        assert result == "+44 20 7946 0958"

    def test_initialization_stores_strategy(self):
        """Test that strategy is stored on the extractor."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        extractor = PhoneExtractor(mock_strategy)

        assert extractor.extraction_strategy is mock_strategy


class TestPhoneExtractorValidation:
    """Tests for PhoneExtractor._validate_phone()."""

    def test_phone_with_dashes_and_parens_counts_digits(self):
        """Non-digit characters in phone are ignored when counting digits."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["(800) 555-1234"]
        extractor = PhoneExtractor(mock_strategy)

        result = extractor.extract("Contact: (800) 555-1234")

        assert result == "(800) 555-1234"

    def test_phone_with_only_symbols_too_short(self):
        """Phone made entirely of symbols (0 digits) fails."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["---"]
        extractor = PhoneExtractor(mock_strategy)

        with pytest.raises(FieldExtractionError, match="does not look like a phone number"):
            extractor.extract("Phone: ---")
