"""Tests for ExperienceAnalyticsExtractor — date parsing, duration, analytics."""

from datetime import date
import pytest

from extractors.experience_analytics_extractor import (
    ExperienceAnalyticsExtractor,
    _years_to_level,
)
from models.work_experience import WorkExperienceEntry
from models.experience_analytics import ExperienceAnalytics


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def _entry(
    company="ACME",
    title="Engineer",
    start_date=None,
    end_date=None,
    duration_months=None,
    skills_used=None,
) -> WorkExperienceEntry:
    return WorkExperienceEntry(
        company=company,
        title=title,
        start_date=start_date,
        end_date=end_date,
        duration_months=duration_months,
        skills_used=skills_used or [],
    )


# ---------------------------------------------------------------------------
# _parse_date
# ---------------------------------------------------------------------------

class TestParseDate:
    """Tests for ExperienceAnalyticsExtractor._parse_date()."""

    def test_parse_iso_date(self):
        result = ExperienceAnalyticsExtractor._parse_date("2023-06-15")
        assert result == date(2023, 6, 15)

    def test_parse_year_month(self):
        result = ExperienceAnalyticsExtractor._parse_date("2021-03")
        assert result == date(2021, 3, 1)

    def test_parse_mm_slash_yyyy(self):
        result = ExperienceAnalyticsExtractor._parse_date("06/2020")
        assert result == date(2020, 6, 1)

    def test_parse_mm_dash_yyyy(self):
        result = ExperienceAnalyticsExtractor._parse_date("01-2019")
        assert result == date(2019, 1, 1)

    def test_parse_month_abbrev_year(self):
        result = ExperienceAnalyticsExtractor._parse_date("Jan 2022")
        assert result == date(2022, 1, 1)

    def test_parse_month_abbrev_year_with_dot(self):
        result = ExperienceAnalyticsExtractor._parse_date("Dec. 2020")
        assert result == date(2020, 12, 1)

    def test_parse_month_full_name_year(self):
        result = ExperienceAnalyticsExtractor._parse_date("March 2018")
        assert result == date(2018, 3, 1)

    def test_parse_bare_year(self):
        result = ExperienceAnalyticsExtractor._parse_date("2017")
        assert result == date(2017, 1, 1)

    def test_parse_present_returns_today(self):
        result = ExperienceAnalyticsExtractor._parse_date("Present")
        assert result == date.today()

    def test_parse_current_returns_today(self):
        result = ExperienceAnalyticsExtractor._parse_date("Current")
        assert result == date.today()

    def test_parse_now_returns_today(self):
        result = ExperienceAnalyticsExtractor._parse_date("now")
        assert result == date.today()

    def test_parse_dash_returns_today(self):
        result = ExperienceAnalyticsExtractor._parse_date("-")
        assert result == date.today()

    def test_parse_none_with_default_today(self):
        result = ExperienceAnalyticsExtractor._parse_date(None, default_today=True)
        assert result == date.today()

    def test_parse_none_without_default(self):
        result = ExperienceAnalyticsExtractor._parse_date(None, default_today=False)
        assert result is None

    def test_parse_none_default_is_false(self):
        """default_today defaults to False, so None input → None output."""
        result = ExperienceAnalyticsExtractor._parse_date(None)
        assert result is None

    def test_parse_empty_string_with_default_today(self):
        result = ExperienceAnalyticsExtractor._parse_date("", default_today=True)
        assert result == date.today()

    def test_parse_invalid_string_returns_none(self):
        result = ExperienceAnalyticsExtractor._parse_date("not a date at all")
        assert result is None

    def test_parse_all_months_abbreviations(self):
        """Test that all 12 month abbreviations are recognized."""
        abbrevs = ["jan", "feb", "mar", "apr", "may", "jun",
                   "jul", "aug", "sep", "oct", "nov", "dec"]
        for i, abbrev in enumerate(abbrevs, 1):
            result = ExperienceAnalyticsExtractor._parse_date(f"{abbrev} 2020")
            assert result is not None, f"{abbrev} not recognized"
            assert result.month == i


# ---------------------------------------------------------------------------
# _resolve_duration
# ---------------------------------------------------------------------------

class TestResolveDuration:
    """Tests for ExperienceAnalyticsExtractor._resolve_duration()."""

    extractor = ExperienceAnalyticsExtractor()

    def test_uses_duration_months_if_set(self):
        """Pre-set duration_months takes priority over date calculation."""
        entry = _entry(
            start_date="Jan 2020",
            end_date="Jan 2022",
            duration_months=30,  # explicitly set
        )
        assert self.extractor._resolve_duration(entry) == 30

    def test_calculates_from_dates(self):
        """Calculates duration when duration_months is None."""
        entry = _entry(start_date="2020-01", end_date="2022-01")
        result = self.extractor._resolve_duration(entry)
        assert result == 24

    def test_calculates_from_dates_partial_year(self):
        """Handles calculation crossing mid-year boundaries."""
        entry = _entry(start_date="2021-06", end_date="2022-03")
        result = self.extractor._resolve_duration(entry)
        assert result == 9

    def test_end_date_present_uses_today(self):
        """end_date='Present' should resolve to today."""
        today = date.today()
        # Use a fixed far-past start to guarantee positive duration
        entry = _entry(start_date="2000-01", end_date="Present")
        result = self.extractor._resolve_duration(entry)
        expected_months = (today.year - 2000) * 12 + today.month - 1
        assert result == expected_months

    def test_end_before_start_returns_zero(self):
        """Negative duration (end before start) returns 0."""
        entry = _entry(start_date="2022-06", end_date="2020-01")
        assert self.extractor._resolve_duration(entry) == 0

    def test_no_dates_no_duration_returns_zero(self):
        """No dates and no duration_months returns 0."""
        entry = _entry()
        assert self.extractor._resolve_duration(entry) == 0

    def test_duration_months_zero_triggers_date_calc(self):
        """duration_months=0 is treated as 'not set', falls through to dates."""
        entry = _entry(start_date="2020-01", end_date="2022-01", duration_months=0)
        result = self.extractor._resolve_duration(entry)
        assert result == 24


# ---------------------------------------------------------------------------
# _infer_career_level
# ---------------------------------------------------------------------------

class TestInferCareerLevel:
    """Tests for ExperienceAnalyticsExtractor._infer_career_level()."""

    def test_cto_title_maps_to_executive(self):
        assert ExperienceAnalyticsExtractor._infer_career_level("CTO", 15) == "Executive"

    def test_vp_title_maps_to_executive(self):
        assert ExperienceAnalyticsExtractor._infer_career_level("VP of Engineering", 10) == "Executive"

    def test_director_title_maps_to_director(self):
        assert ExperienceAnalyticsExtractor._infer_career_level("Director of Product", 8) == "Director"

    def test_head_of_title_maps_to_director(self):
        assert ExperienceAnalyticsExtractor._infer_career_level("Head of Engineering", 7) == "Director"

    def test_manager_title_maps_to_manager(self):
        assert ExperienceAnalyticsExtractor._infer_career_level("Engineering Manager", 6) == "Manager"

    def test_lead_title_maps_to_manager(self):
        assert ExperienceAnalyticsExtractor._infer_career_level("Tech Lead", 5) == "Manager"

    def test_senior_title_maps_to_senior(self):
        assert ExperienceAnalyticsExtractor._infer_career_level("Senior Software Engineer", 4) == "Senior"

    def test_sr_abbrev_title_maps_to_senior(self):
        assert ExperienceAnalyticsExtractor._infer_career_level("Sr. Developer", 3) == "Senior"

    def test_junior_title_maps_to_junior(self):
        assert ExperienceAnalyticsExtractor._infer_career_level("Junior Developer", 1) == "Junior"

    def test_intern_title_maps_to_junior(self):
        assert ExperienceAnalyticsExtractor._infer_career_level("Software Intern", 0.5) == "Junior"

    def test_empty_title_falls_back_to_years(self):
        """Empty title uses the years-based heuristic."""
        assert ExperienceAnalyticsExtractor._infer_career_level("", 4) == "Senior"

    def test_unknown_title_falls_back_to_years(self):
        """Unrecognized title uses the years-based heuristic."""
        assert ExperienceAnalyticsExtractor._infer_career_level("Rockstar Coder", 1) == "Mid"


class TestYearsToLevel:
    """Tests for _years_to_level fallback function."""

    def test_less_than_one_year_is_junior(self):
        assert _years_to_level(0.5) == "Junior"

    def test_one_year_is_mid(self):
        assert _years_to_level(1.0) == "Mid"

    def test_two_years_is_mid(self):
        assert _years_to_level(2.9) == "Mid"

    def test_three_years_is_senior(self):
        assert _years_to_level(3.0) == "Senior"

    def test_five_years_is_senior(self):
        assert _years_to_level(5.9) == "Senior"

    def test_six_years_is_lead(self):
        assert _years_to_level(6.0) == "Lead"

    def test_nine_years_is_lead(self):
        assert _years_to_level(9.9) == "Lead"

    def test_ten_years_is_executive(self):
        assert _years_to_level(10.0) == "Executive"


# ---------------------------------------------------------------------------
# compute()
# ---------------------------------------------------------------------------

class TestExperienceAnalyticsCompute:
    """Tests for ExperienceAnalyticsExtractor.compute()."""

    extractor = ExperienceAnalyticsExtractor()

    def test_empty_list_returns_default_analytics(self):
        result = self.extractor.compute([])

        assert isinstance(result, ExperienceAnalytics)
        assert result.total_years == 0.0
        assert result.years_by_role == {}
        assert result.years_by_company == {}
        assert result.skills_with_years == {}

    def test_single_entry_with_duration_months(self):
        """One entry with explicit duration_months = 24."""
        entry = _entry(
            company="Corp A",
            title="Engineer",
            duration_months=24,
            skills_used=["Python"],
        )

        result = self.extractor.compute([entry])

        assert result.total_years == 2.0
        assert result.years_by_role == {"Engineer": 2.0}
        assert result.years_by_company == {"Corp A": 2.0}
        assert result.skills_with_years == {"Python": 2.0}

    def test_multiple_entries_accumulate_totals(self):
        """Two entries: 12 + 24 months = 36 months = 3.0 years."""
        entries = [
            _entry(company="Corp A", title="Junior Dev", duration_months=12),
            _entry(company="Corp B", title="Senior Dev", duration_months=24),
        ]

        result = self.extractor.compute(entries)

        assert result.total_years == 3.0

    def test_years_by_role_accumulates_same_title(self):
        """Same title at two different companies → totalled under same key."""
        entries = [
            _entry(company="Corp A", title="SWE", duration_months=12),
            _entry(company="Corp B", title="SWE", duration_months=24),
        ]

        result = self.extractor.compute(entries)

        assert result.years_by_role["SWE"] == 3.0

    def test_years_by_company_accumulates_multiple_stints(self):
        """Two stints at the same company aggregate correctly."""
        entries = [
            _entry(company="MegaCorp", title="Engineer", duration_months=12),
            _entry(company="MegaCorp", title="Senior Eng", duration_months=18),
        ]

        result = self.extractor.compute(entries)

        assert result.years_by_company["MegaCorp"] == 2.5

    def test_skills_with_years_aggregated_across_roles(self):
        """A skill appearing in two roles has its years summed."""
        entries = [
            _entry(company="A", title="Dev", duration_months=12, skills_used=["Python", "SQL"]),
            _entry(company="B", title="Eng", duration_months=24, skills_used=["Python"]),
        ]

        result = self.extractor.compute(entries)

        assert result.skills_with_years["Python"] == 3.0  # 1 + 2 years
        assert result.skills_with_years["SQL"] == 1.0

    def test_most_recent_title_is_first_entry(self):
        """The first entry in the list is used as the most recent title."""
        entries = [
            _entry(company="Latest", title="Staff Engineer", duration_months=6),
            _entry(company="Previous", title="Junior Developer", duration_months=12),
        ]

        result = self.extractor.compute(entries)

        assert result.most_recent_title == "Staff Engineer"

    def test_career_level_inferred_from_most_recent_title(self):
        """Career level is inferred from the most recent title."""
        entries = [
            _entry(title="Senior Software Engineer", duration_months=36),
        ]

        result = self.extractor.compute(entries)

        assert result.career_level == "Senior"

    def test_entries_without_title_skipped_in_years_by_role(self):
        """Entries with no title are not added to years_by_role."""
        entry = _entry(company="Corp A", title="", duration_months=12)

        result = self.extractor.compute([entry])

        assert result.years_by_role == {}
        assert result.years_by_company == {"Corp A": 1.0}

    def test_entries_without_company_skipped_in_years_by_company(self):
        """Entries with no company are not added to years_by_company."""
        entry = _entry(company="", title="Consultant", duration_months=12)

        result = self.extractor.compute([entry])

        assert result.years_by_company == {}
        assert result.years_by_role == {"Consultant": 1.0}

    def test_blank_skills_are_filtered(self):
        """Whitespace-only skill names are not added to skills_with_years."""
        entry = _entry(
            company="Corp",
            title="Dev",
            duration_months=12,
            skills_used=["  ", "", "Python"],
        )

        result = self.extractor.compute([entry])

        assert "  " not in result.skills_with_years
        assert "" not in result.skills_with_years
        assert "Python" in result.skills_with_years

    def test_uses_date_range_when_no_duration_months(self):
        """Duration computed from start/end dates when duration_months is absent."""
        entry = _entry(
            company="Corp",
            title="Dev",
            start_date="2020-01",
            end_date="2022-01",
        )

        result = self.extractor.compute([entry])

        assert result.total_years == 2.0
