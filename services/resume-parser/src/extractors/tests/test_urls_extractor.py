"""Tests for UrlsExtractor."""

import pytest
from unittest.mock import Mock

from extractors.urls_extractor import UrlsExtractor
from interfaces import ExtractionStrategy, FieldType
from exceptions import FieldExtractionError


class TestUrlsExtractor:
    """Tests for UrlsExtractor."""

    def test_extract_linkedin_url_success(self):
        """Test successful LinkedIn URL extraction."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["https://linkedin.com/in/johndoe"]
        extractor = UrlsExtractor(mock_strategy, FieldType.LINKEDIN_URL)

        result = extractor.extract("Profile: https://linkedin.com/in/johndoe")

        assert result == ["https://linkedin.com/in/johndoe"]

    def test_extract_github_url_success(self):
        """Test successful GitHub URL extraction."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["https://github.com/johndoe"]
        extractor = UrlsExtractor(mock_strategy, FieldType.GITHUB_URL)

        result = extractor.extract("GitHub: https://github.com/johndoe")

        assert result == ["https://github.com/johndoe"]

    def test_extract_multiple_urls_returned(self):
        """Test that multiple URLs are all returned."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = [
            "https://example.com/blog",
            "https://portfolio.dev/johndoe",
        ]
        extractor = UrlsExtractor(mock_strategy, FieldType.OTHER_URLS)

        result = extractor.extract("Websites: ...")

        assert len(result) == 2
        assert "https://example.com/blog" in result

    def test_extract_empty_results_returns_empty_list(self):
        """Test that empty strategy results returns empty list (not error)."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = []
        extractor = UrlsExtractor(mock_strategy, FieldType.LINKEDIN_URL)

        result = extractor.extract("No LinkedIn here")

        assert result == []

    def test_extract_filters_blank_urls(self):
        """Test that blank or whitespace-only URLs are filtered out."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["https://github.com/x", "  ", ""]
        extractor = UrlsExtractor(mock_strategy, FieldType.GITHUB_URL)

        result = extractor.extract("GitHub: https://github.com/x")

        assert result == ["https://github.com/x"]

    def test_extract_strips_url_whitespace(self):
        """Test that URL whitespace is stripped."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["  https://linkedin.com/in/x  "]
        extractor = UrlsExtractor(mock_strategy, FieldType.LINKEDIN_URL)

        result = extractor.extract("Profile link...")

        assert result == ["https://linkedin.com/in/x"]

    def test_extract_empty_text_raises_error(self):
        """Test that empty input raises FieldExtractionError."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        extractor = UrlsExtractor(mock_strategy, FieldType.LINKEDIN_URL)

        with pytest.raises(FieldExtractionError, match="Input text is empty"):
            extractor.extract("")

    def test_extract_whitespace_only_raises_error(self):
        """Test that whitespace-only input raises FieldExtractionError."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        extractor = UrlsExtractor(mock_strategy, FieldType.GITHUB_URL)

        with pytest.raises(FieldExtractionError, match="Input text is empty"):
            extractor.extract("   ")

    def test_extract_strategy_exception_wrapped(self):
        """Test that strategy exceptions are wrapped in FieldExtractionError."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.side_effect = RuntimeError("regex failed")
        extractor = UrlsExtractor(mock_strategy, FieldType.LINKEDIN_URL)

        with pytest.raises(FieldExtractionError, match="URL extraction failed"):
            extractor.extract("Some resume text")

    def test_field_type_stored(self):
        """Test that field_type is stored on the extractor."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        extractor = UrlsExtractor(mock_strategy, FieldType.PORTFOLIO_URL)

        assert extractor.field_type == FieldType.PORTFOLIO_URL

    def test_initialization_stores_strategy(self):
        """Test that strategy is stored on the extractor."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        extractor = UrlsExtractor(mock_strategy, FieldType.OTHER_URLS)

        assert extractor.extraction_strategy is mock_strategy
