"""Tests for ListFieldExtractor."""

import pytest
from unittest.mock import Mock

from extractors.list_field_extractor import ListFieldExtractor
from interfaces import ExtractionStrategy, FieldType
from exceptions import FieldExtractionError


class TestListFieldExtractor:
    """Tests for ListFieldExtractor."""

    def test_extract_interests_success(self):
        """Test successful interests extraction."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["hiking", "photography", "open source"]
        extractor = ListFieldExtractor(mock_strategy, FieldType.INTERESTS)

        result = extractor.extract("Interests: hiking, photography, open source")

        assert result == ["hiking", "photography", "open source"]
        mock_strategy.extract.assert_called_once()

    def test_extract_languages_success(self):
        """Test successful languages extraction."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["English", "Spanish", "French"]
        extractor = ListFieldExtractor(mock_strategy, FieldType.LANGUAGES)

        result = extractor.extract("Languages: English, Spanish, French")

        assert result == ["English", "Spanish", "French"]

    def test_extract_awards_success(self):
        """Test successful awards extraction."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["Employee of the Year 2022", "Hackathon Winner"]
        extractor = ListFieldExtractor(mock_strategy, FieldType.AWARDS)

        result = extractor.extract("Awards: ...")

        assert result == ["Employee of the Year 2022", "Hackathon Winner"]

    def test_extract_returns_empty_list_when_no_results(self):
        """Test that empty strategy results returns empty list."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = []
        extractor = ListFieldExtractor(mock_strategy, FieldType.INTERESTS)

        result = extractor.extract("No hobbies mentioned")

        assert result == []

    def test_extract_filters_blank_items(self):
        """Test that blank/whitespace items are filtered from results."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["hiking", "", "  ", "photography"]
        extractor = ListFieldExtractor(mock_strategy, FieldType.INTERESTS)

        result = extractor.extract("Interests: hiking, photography")

        assert result == ["hiking", "photography"]

    def test_extract_strips_whitespace_from_items(self):
        """Test that item whitespace is stripped."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["  English  ", " Spanish "]
        extractor = ListFieldExtractor(mock_strategy, FieldType.LANGUAGES)

        result = extractor.extract("Languages: English, Spanish")

        assert result == ["English", "Spanish"]

    def test_extract_empty_text_raises_error(self):
        """Test that empty input raises FieldExtractionError."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        extractor = ListFieldExtractor(mock_strategy, FieldType.INTERESTS)

        with pytest.raises(FieldExtractionError):
            extractor.extract("")

    def test_extract_whitespace_only_raises_error(self):
        """Test that whitespace-only input raises FieldExtractionError."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        extractor = ListFieldExtractor(mock_strategy, FieldType.LANGUAGES)

        with pytest.raises(FieldExtractionError):
            extractor.extract("   ")

    def test_extract_strategy_exception_wrapped(self):
        """Test that strategy exceptions are wrapped in FieldExtractionError."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.side_effect = RuntimeError("LLM timeout")
        extractor = ListFieldExtractor(mock_strategy, FieldType.AWARDS)

        with pytest.raises(FieldExtractionError):
            extractor.extract("Some resume text")

    def test_field_type_stored(self):
        """Test that field_type is stored on the extractor."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        extractor = ListFieldExtractor(mock_strategy, FieldType.INTERESTS)

        assert extractor.field_type == FieldType.INTERESTS

    def test_initialization_stores_strategy(self):
        """Test that strategy is stored on the extractor."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        extractor = ListFieldExtractor(mock_strategy, FieldType.LANGUAGES)

        assert extractor.extraction_strategy is mock_strategy
