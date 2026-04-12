"""Tests for StructuredExtractor base class."""

import json
import pytest
from unittest.mock import Mock

from extractors.structured_extractor import StructuredExtractor
from interfaces import ExtractionStrategy
from exceptions import FieldExtractionError


# ---------------------------------------------------------------------------
# Minimal concrete subclass used across tests
# ---------------------------------------------------------------------------

class _SimpleItem:
    def __init__(self, name: str, value: int):
        self.name = name
        self.value = value


class _ConcreteExtractor(StructuredExtractor[_SimpleItem]):
    """Minimal concrete subclass for testing."""

    def _field_name(self) -> str:
        return "SimpleItem"

    def _parse_item(self, data: dict) -> _SimpleItem:
        return _SimpleItem(name=data["name"], value=int(data["value"]))


class TestStructuredExtractorAbstraction:
    """Ensure the abstract contract is enforced."""

    def test_cannot_instantiate_without_implementing_abstract_methods(self):
        """Direct instantiation of StructuredExtractor should raise TypeError."""
        mock_strategy = Mock(spec=ExtractionStrategy)

        class IncompleteExtractor(StructuredExtractor[_SimpleItem]):
            pass  # does NOT implement _parse_item or _field_name

        with pytest.raises(TypeError):
            IncompleteExtractor(mock_strategy)

    def test_concrete_subclass_instantiates_successfully(self):
        """Concrete subclass with all methods implemented can be created."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        extractor = _ConcreteExtractor(mock_strategy)

        assert extractor.extraction_strategy is mock_strategy


class TestStructuredExtractorExtract:
    """Tests for StructuredExtractor.extract()."""

    def _make_json(self, name: str, value: int) -> str:
        return json.dumps({"name": name, "value": value})

    def test_extract_success_single_item(self):
        """Test extracting a single well-formed JSON string."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = [self._make_json("alpha", 1)]
        extractor = _ConcreteExtractor(mock_strategy)

        results = extractor.extract("Some text")

        assert len(results) == 1
        assert results[0].name == "alpha"
        assert results[0].value == 1

    def test_extract_success_multiple_items(self):
        """Test extracting multiple JSON strings."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = [
            self._make_json("alpha", 1),
            self._make_json("beta", 2),
            self._make_json("gamma", 3),
        ]
        extractor = _ConcreteExtractor(mock_strategy)

        results = extractor.extract("Some text")

        assert len(results) == 3
        assert results[1].name == "beta"
        assert results[2].value == 3

    def test_extract_empty_text_raises_error(self):
        """Test that empty input raises FieldExtractionError."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        extractor = _ConcreteExtractor(mock_strategy)

        with pytest.raises(FieldExtractionError, match="Input text is empty"):
            extractor.extract("")

    def test_extract_whitespace_only_raises_error(self):
        """Test that whitespace-only input raises FieldExtractionError."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        extractor = _ConcreteExtractor(mock_strategy)

        with pytest.raises(FieldExtractionError, match="Input text is empty"):
            extractor.extract("   ")

    def test_extract_strategy_exception_wrapped(self):
        """Test that strategy exceptions are wrapped in FieldExtractionError."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.side_effect = RuntimeError("LLM error")
        extractor = _ConcreteExtractor(mock_strategy)

        with pytest.raises(FieldExtractionError, match="SimpleItem LLM extraction failed"):
            extractor.extract("Some text")

    def test_extract_malformed_json_skipped_not_raised(self):
        """Test that a malformed JSON entry is skipped (logged), not raised."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = [
            self._make_json("good", 1),
            "this is not json {{{",
            self._make_json("also_good", 2),
        ]
        extractor = _ConcreteExtractor(mock_strategy)

        results = extractor.extract("Some text")

        assert len(results) == 2
        assert results[0].name == "good"
        assert results[1].name == "also_good"

    def test_extract_all_malformed_returns_empty_list(self):
        """Test that all malformed entries returns an empty list."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["not json", "also not json"]
        extractor = _ConcreteExtractor(mock_strategy)

        results = extractor.extract("Some text")

        assert results == []

    def test_extract_strategy_returns_empty_list(self):
        """Test that empty strategy results returns empty list."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = []
        extractor = _ConcreteExtractor(mock_strategy)

        results = extractor.extract("Some text")

        assert results == []

    def test_extract_accepts_dict_directly_not_just_string(self):
        """Test that raw dict items (not strings) are also accepted."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = [{"name": "raw_dict", "value": 99}]
        extractor = _ConcreteExtractor(mock_strategy)

        results = extractor.extract("Some text")

        assert len(results) == 1
        assert results[0].name == "raw_dict"
        assert results[0].value == 99

    def test_extract_item_with_parse_error_skipped(self):
        """Test that _parse_item exceptions are caught and the item is skipped."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        # 'value' is not castable to int → _parse_item will raise ValueError
        mock_strategy.extract.return_value = [
            json.dumps({"name": "good", "value": 5}),
            json.dumps({"name": "bad", "value": "not_an_int"}),
        ]
        extractor = _ConcreteExtractor(mock_strategy)

        results = extractor.extract("Some text")

        # "bad" entry causes ValueError in _parse_item, skipped
        assert len(results) == 1
        assert results[0].name == "good"
