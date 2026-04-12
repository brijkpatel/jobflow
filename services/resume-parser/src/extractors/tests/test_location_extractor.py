"""Tests for LocationExtractor."""

import pytest
from unittest.mock import Mock

from extractors.location_extractor import LocationExtractor
from interfaces import ExtractionStrategy
from exceptions import FieldExtractionError


class TestLocationExtractor:
    """Tests for LocationExtractor."""

    def test_extract_success(self):
        """Test successful location extraction."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["San Francisco, CA"]
        extractor = LocationExtractor(mock_strategy)

        result = extractor.extract("Lives in San Francisco, CA")

        assert result == "San Francisco, CA"
        mock_strategy.extract.assert_called_once()

    def test_extract_returns_first_result(self):
        """Test that only the first location is returned."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["New York, NY", "London, UK"]
        extractor = LocationExtractor(mock_strategy)

        result = extractor.extract("Based in New York, NY")

        assert result == "New York, NY"

    def test_extract_strips_whitespace_from_result(self):
        """Test that whitespace is stripped from extracted location."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["  Austin, TX  "]
        extractor = LocationExtractor(mock_strategy)

        result = extractor.extract("Location: Austin, TX")

        assert result == "Austin, TX"

    def test_extract_strips_input_text(self):
        """Test that input text whitespace is stripped before strategy call."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["Berlin"]
        extractor = LocationExtractor(mock_strategy)

        result = extractor.extract("   Berlin   ")

        assert result == "Berlin"

    def test_extract_empty_text_raises_error(self):
        """Test that empty input raises FieldExtractionError."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        extractor = LocationExtractor(mock_strategy)

        with pytest.raises(FieldExtractionError, match="Input text is empty"):
            extractor.extract("")

    def test_extract_whitespace_only_raises_error(self):
        """Test that whitespace-only input raises FieldExtractionError."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        extractor = LocationExtractor(mock_strategy)

        with pytest.raises(FieldExtractionError, match="Input text is empty"):
            extractor.extract("   ")

    def test_extract_no_results_raises_error(self):
        """Test that an empty results list raises FieldExtractionError."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = []
        extractor = LocationExtractor(mock_strategy)

        with pytest.raises(FieldExtractionError, match="No location found"):
            extractor.extract("Resume without a location")

    def test_extract_strategy_exception_wrapped(self):
        """Test that strategy exceptions are wrapped in FieldExtractionError."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.side_effect = ValueError("NER failed")
        extractor = LocationExtractor(mock_strategy)

        with pytest.raises(FieldExtractionError, match="Location extraction failed"):
            extractor.extract("Some resume text")

    def test_initialization_stores_strategy(self):
        """Test that strategy is stored on the extractor."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        extractor = LocationExtractor(mock_strategy)

        assert extractor.extraction_strategy is mock_strategy
