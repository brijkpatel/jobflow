"""Tests for SummaryExtractor."""

import pytest
from unittest.mock import Mock

from extractors.summary_extractor import SummaryExtractor
from interfaces import ExtractionStrategy
from exceptions import FieldExtractionError


class TestSummaryExtractor:
    """Tests for SummaryExtractor."""

    def test_extract_success(self):
        """Test successful summary extraction."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = [
            "Experienced software engineer with 8 years in Python and cloud infrastructure."
        ]
        extractor = SummaryExtractor(mock_strategy)

        result = extractor.extract("SUMMARY\nExperienced software engineer...")

        assert result == "Experienced software engineer with 8 years in Python and cloud infrastructure."
        mock_strategy.extract.assert_called_once()

    def test_extract_returns_first_result(self):
        """Test that only the first result is returned."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["First summary.", "Second summary."]
        extractor = SummaryExtractor(mock_strategy)

        result = extractor.extract("Some resume text")

        assert result == "First summary."

    def test_extract_strips_result_whitespace(self):
        """Test that whitespace is stripped from the extracted summary."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["  Passionate developer.  "]
        extractor = SummaryExtractor(mock_strategy)

        result = extractor.extract("Some text")

        assert result == "Passionate developer."

    def test_extract_empty_text_raises_error(self):
        """Test that empty input raises FieldExtractionError."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        extractor = SummaryExtractor(mock_strategy)

        with pytest.raises(FieldExtractionError, match="Input text is empty"):
            extractor.extract("")

    def test_extract_whitespace_only_raises_error(self):
        """Test that whitespace-only input raises FieldExtractionError."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        extractor = SummaryExtractor(mock_strategy)

        with pytest.raises(FieldExtractionError, match="Input text is empty"):
            extractor.extract("   ")

    def test_extract_no_results_raises_error(self):
        """Test that empty results list raises FieldExtractionError."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = []
        extractor = SummaryExtractor(mock_strategy)

        with pytest.raises(FieldExtractionError, match="No summary found"):
            extractor.extract("A resume with no identifiable summary")

    def test_extract_strategy_exception_wrapped(self):
        """Test that strategy exceptions are wrapped in FieldExtractionError."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.side_effect = ConnectionError("API timeout")
        extractor = SummaryExtractor(mock_strategy)

        with pytest.raises(FieldExtractionError, match="Summary extraction failed"):
            extractor.extract("Some resume text")

    def test_initialization_stores_strategy(self):
        """Test that strategy is stored on the extractor."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        extractor = SummaryExtractor(mock_strategy)

        assert extractor.extraction_strategy is mock_strategy
