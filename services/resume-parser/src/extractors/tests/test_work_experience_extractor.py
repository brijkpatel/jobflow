"""Tests for WorkExperienceExtractor."""

import json
import pytest
from unittest.mock import Mock

from extractors.work_experience_extractor import (
    WorkExperienceExtractor,
    _to_int,
    _to_str_list,
)
from models.work_experience import WorkExperienceEntry
from interfaces import ExtractionStrategy
from exceptions import FieldExtractionError


def _make_entry(**kwargs) -> str:
    """Helper: serialise a dict to a JSON string for the mock strategy."""
    return json.dumps(kwargs)


class TestWorkExperienceExtractorExtract:
    """Tests for WorkExperienceExtractor.extract()."""

    def test_extract_single_full_entry(self):
        """Test extraction of a complete work experience entry."""
        raw = _make_entry(
            company="Acme Corp",
            title="Senior Engineer",
            location="San Francisco, CA",
            start_date="Jan 2020",
            end_date="Present",
            duration_months=50,
            description="Led backend development",
            responsibilities=["Designed APIs", "Mentored juniors"],
            skills_used=["Python", "Docker"],
        )
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = [raw]
        extractor = WorkExperienceExtractor(mock_strategy)

        results = extractor.extract("Work history...")

        assert len(results) == 1
        entry = results[0]
        assert isinstance(entry, WorkExperienceEntry)
        assert entry.company == "Acme Corp"
        assert entry.title == "Senior Engineer"
        assert entry.location == "San Francisco, CA"
        assert entry.start_date == "Jan 2020"
        assert entry.end_date == "Present"
        assert entry.duration_months == 50
        assert entry.description == "Led backend development"
        assert entry.responsibilities == ["Designed APIs", "Mentored juniors"]
        assert entry.skills_used == ["Python", "Docker"]

    def test_extract_partial_entry_uses_defaults(self):
        """Test that missing optional fields default gracefully."""
        raw = _make_entry(company="Startup", title="Dev")
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = [raw]
        extractor = WorkExperienceExtractor(mock_strategy)

        results = extractor.extract("Work history...")

        assert len(results) == 1
        entry = results[0]
        assert entry.company == "Startup"
        assert entry.title == "Dev"
        assert entry.location is None
        assert entry.start_date is None
        assert entry.end_date is None
        assert entry.duration_months is None
        assert entry.responsibilities == []
        assert entry.skills_used == []

    def test_extract_multiple_entries(self):
        """Test extraction of multiple work experience entries."""
        raw1 = _make_entry(company="Company A", title="Engineer")
        raw2 = _make_entry(company="Company B", title="Senior Engineer")
        raw3 = _make_entry(company="Company C", title="Staff Engineer")
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = [raw1, raw2, raw3]
        extractor = WorkExperienceExtractor(mock_strategy)

        results = extractor.extract("Work history...")

        assert len(results) == 3
        assert results[0].company == "Company A"
        assert results[2].title == "Staff Engineer"

    def test_extract_malformed_entry_skipped(self):
        """Test that a malformed JSON entry is skipped and others processed."""
        raw_good = _make_entry(company="Good Corp", title="Engineer")
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = [raw_good, "{{{ bad json }}}"]
        extractor = WorkExperienceExtractor(mock_strategy)

        results = extractor.extract("Work history...")

        assert len(results) == 1
        assert results[0].company == "Good Corp"

    def test_extract_empty_text_raises_error(self):
        """Test that empty input raises FieldExtractionError."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        extractor = WorkExperienceExtractor(mock_strategy)

        with pytest.raises(FieldExtractionError, match="Input text is empty"):
            extractor.extract("")

    def test_extract_skills_used_populated(self):
        """Test that skills_used list is correctly parsed."""
        raw = _make_entry(
            company="TechCo",
            title="Backend Developer",
            skills_used=["Python", "PostgreSQL", "Redis"],
        )
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = [raw]
        extractor = WorkExperienceExtractor(mock_strategy)

        results = extractor.extract("Resume text")

        assert results[0].skills_used == ["Python", "PostgreSQL", "Redis"]

    def test_extract_responsibilities_populated(self):
        """Test that responsibilities list is correctly parsed."""
        raw = _make_entry(
            company="BigBank",
            title="QA Engineer",
            responsibilities=["Wrote test plans", "Automated regression suite"],
        )
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = [raw]
        extractor = WorkExperienceExtractor(mock_strategy)

        results = extractor.extract("Resume text")

        assert results[0].responsibilities == ["Wrote test plans", "Automated regression suite"]

    def test_field_name_is_work_experience(self):
        """Test that _field_name returns the expected string."""
        mock_strategy = Mock(spec=ExtractionStrategy)
        extractor = WorkExperienceExtractor(mock_strategy)

        assert extractor._field_name() == "WorkExperience"


class TestToInt:
    """Tests for _to_int helper."""

    def test_converts_integer(self):
        assert _to_int(12) == 12

    def test_converts_string_integer(self):
        assert _to_int("36") == 36

    def test_returns_none_for_none(self):
        assert _to_int(None) is None

    def test_returns_none_for_non_numeric_string(self):
        assert _to_int("not_a_number") is None

    def test_returns_none_for_invalid_type(self):
        assert _to_int([1, 2]) is None


class TestToStrList:
    """Tests for _to_str_list helper."""

    def test_converts_list_of_strings(self):
        assert _to_str_list(["a", "b", "c"]) == ["a", "b", "c"]

    def test_strips_whitespace_from_items(self):
        assert _to_str_list(["  a  ", " b"]) == ["a", "b"]

    def test_filters_out_empty_items(self):
        assert _to_str_list(["a", "", None, "b"]) == ["a", "b"]

    def test_non_list_returns_empty_list(self):
        assert _to_str_list("not a list") == []

    def test_none_returns_empty_list(self):
        assert _to_str_list(None) == []

    def test_converts_non_string_items_to_str(self):
        result = _to_str_list([1, 2, 3])
        assert result == ["1", "2", "3"]
