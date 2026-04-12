"""Integration tests for ResumeExtractor with new field types.

These tests cover the coordinator's handling of contact info, structured
sections, list fields, analytics computation, and fallback behaviour for
all the new field types added in the comprehensive expansion.
"""

import pytest
from unittest.mock import Mock, MagicMock

from coordinators.resume_extractor import ResumeExtractor
from interfaces import FieldExtractor, FieldType
from models import (
    ResumeData,
    ContactInfo,
    WorkExperienceEntry,
    EducationEntry,
    CertificationEntry,
    ProjectEntry,
    VolunteerEntry,
    PublicationEntry,
    ExperienceAnalytics,
)
from extractors.experience_analytics_extractor import ExperienceAnalyticsExtractor


# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------

def _mock_extractor(return_value):
    """Return a mock FieldExtractor whose .extract() returns the given value."""
    m = Mock(spec=FieldExtractor)
    m.extract.return_value = return_value
    return m


def _failing_extractor(error_msg="extraction failed"):
    """Return a mock FieldExtractor whose .extract() raises an exception."""
    m = Mock(spec=FieldExtractor)
    m.extract.side_effect = Exception(error_msg)
    return m


def _base_extractors(extra: dict = None):
    """Return the minimum required extractors, with optional extra entries."""
    base = {
        FieldType.NAME: [_mock_extractor("John Doe")],
        FieldType.EMAIL: [_mock_extractor("john@example.com")],
        FieldType.SKILLS: [_mock_extractor(["Python", "SQL"])],
    }
    if extra:
        base.update(extra)
    return base


# ---------------------------------------------------------------------------
# Contact fields
# ---------------------------------------------------------------------------

class TestResumeExtractorContactFields:
    """Test extraction and assembly of ContactInfo fields."""

    def test_contact_info_built_with_all_fields(self):
        """Full ContactInfo is built when all contact fields are present."""
        extractors = _base_extractors({
            FieldType.PHONE: [_mock_extractor("+1-800-555-0100")],
            FieldType.LOCATION: [_mock_extractor("Austin, TX")],
            FieldType.LINKEDIN_URL: [_mock_extractor(["https://linkedin.com/in/jdoe"])],
            FieldType.GITHUB_URL: [_mock_extractor(["https://github.com/jdoe"])],
            FieldType.PORTFOLIO_URL: [_mock_extractor(["https://jdoe.dev"])],
            FieldType.OTHER_URLS: [_mock_extractor(["https://blog.jdoe.dev"])],
        })
        coord = ResumeExtractor(extractors)

        result = coord.extract("John Doe resume text")

        assert isinstance(result.contact, ContactInfo)
        assert result.contact.phone == "+1-800-555-0100"
        assert result.contact.location == "Austin, TX"
        assert result.contact.linkedin_url == "https://linkedin.com/in/jdoe"
        assert result.contact.github_url == "https://github.com/jdoe"
        assert result.contact.portfolio_url == "https://jdoe.dev"
        assert result.contact.other_urls == ["https://blog.jdoe.dev"]

    def test_contact_info_built_even_when_no_contact_extractors(self):
        """ContactInfo is still created (with None fields) when no contact extractors."""
        coord = ResumeExtractor(_base_extractors())

        result = coord.extract("Minimal resume text")

        assert isinstance(result.contact, ContactInfo)
        assert result.contact.phone is None
        assert result.contact.location is None

    def test_contact_field_failure_returns_none_not_raises(self):
        """A failing contact extractor does not abort the whole extraction."""
        extractors = _base_extractors({
            FieldType.PHONE: [_failing_extractor()],
        })
        coord = ResumeExtractor(extractors)

        result = coord.extract("Resume text")

        assert result.contact.phone is None
        assert result.name == "John Doe"  # other fields unaffected


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

class TestResumeExtractorSummary:
    """Test extraction of professional summary."""

    def test_summary_extracted(self):
        extractors = _base_extractors({
            FieldType.SUMMARY: [_mock_extractor("10 years of backend engineering experience.")],
        })
        coord = ResumeExtractor(extractors)

        result = coord.extract("Summary: 10 years...")

        assert result.summary == "10 years of backend engineering experience."

    def test_summary_none_when_no_extractor(self):
        coord = ResumeExtractor(_base_extractors())

        result = coord.extract("Resume text")

        assert result.summary is None

    def test_summary_none_on_failure(self):
        extractors = _base_extractors({
            FieldType.SUMMARY: [_failing_extractor()],
        })
        coord = ResumeExtractor(extractors)

        result = coord.extract("Resume text")

        assert result.summary is None


# ---------------------------------------------------------------------------
# Structured sections
# ---------------------------------------------------------------------------

class TestResumeExtractorStructuredSections:
    """Test extraction of structured list sections."""

    def _make_work_entry(self):
        return WorkExperienceEntry(
            company="ACME", title="Engineer",
            start_date="2020-01", end_date="Present", duration_months=48,
            skills_used=["Python"],
        )

    def test_work_experience_extracted(self):
        entry = self._make_work_entry()
        extractors = _base_extractors({
            FieldType.WORK_EXPERIENCE: [_mock_extractor([entry])],
        })
        coord = ResumeExtractor(extractors)

        result = coord.extract("Resume text")

        assert result.work_experience is not None
        assert len(result.work_experience) == 1
        assert result.work_experience[0].company == "ACME"

    def test_education_extracted(self):
        edu = EducationEntry(institution="MIT", degree="B.Sc", field_of_study="CS")
        extractors = _base_extractors({
            FieldType.EDUCATION: [_mock_extractor([edu])],
        })
        coord = ResumeExtractor(extractors)

        result = coord.extract("Resume text")

        assert result.education is not None
        assert result.education[0].institution == "MIT"

    def test_certifications_extracted(self):
        cert = CertificationEntry(name="AWS SAA", issuing_organization="Amazon")
        extractors = _base_extractors({
            FieldType.CERTIFICATIONS: [_mock_extractor([cert])],
        })
        coord = ResumeExtractor(extractors)

        result = coord.extract("Resume text")

        assert result.certifications is not None
        assert result.certifications[0].name == "AWS SAA"

    def test_projects_extracted(self):
        proj = ProjectEntry(name="OpenResume", description="A parser")
        extractors = _base_extractors({
            FieldType.PROJECTS: [_mock_extractor([proj])],
        })
        coord = ResumeExtractor(extractors)

        result = coord.extract("Resume text")

        assert result.projects is not None
        assert result.projects[0].name == "OpenResume"

    def test_volunteer_extracted(self):
        vol = VolunteerEntry(organization="RedCross", role="Coordinator")
        extractors = _base_extractors({
            FieldType.VOLUNTEER_EXPERIENCE: [_mock_extractor([vol])],
        })
        coord = ResumeExtractor(extractors)

        result = coord.extract("Resume text")

        assert result.volunteer_experience is not None
        assert result.volunteer_experience[0].organization == "RedCross"

    def test_publications_extracted(self):
        pub = PublicationEntry(title="Advances in NLP", date="2023")
        extractors = _base_extractors({
            FieldType.PUBLICATIONS: [_mock_extractor([pub])],
        })
        coord = ResumeExtractor(extractors)

        result = coord.extract("Resume text")

        assert result.publications is not None
        assert result.publications[0].title == "Advances in NLP"

    def test_structured_section_empty_when_no_extractor(self):
        """Without an extractor, structured list fields default to []."""
        coord = ResumeExtractor(_base_extractors())

        result = coord.extract("Resume text")

        assert result.work_experience == []
        assert result.education == []
        assert result.certifications == []
        assert result.projects == []

    def test_structured_section_empty_on_failure(self):
        """A failing structured extractor returns [] for list fields."""
        extractors = _base_extractors({
            FieldType.WORK_EXPERIENCE: [_failing_extractor()],
        })
        coord = ResumeExtractor(extractors)

        result = coord.extract("Resume text")

        assert result.work_experience == []


# ---------------------------------------------------------------------------
# List fields (interests, languages, awards)
# ---------------------------------------------------------------------------

class TestResumeExtractorListFields:
    """Test extraction of plain string list fields."""

    def test_interests_extracted(self):
        extractors = _base_extractors({
            FieldType.INTERESTS: [_mock_extractor(["hiking", "photography"])],
        })
        coord = ResumeExtractor(extractors)

        result = coord.extract("Resume text")

        assert result.interests == ["hiking", "photography"]

    def test_languages_extracted(self):
        extractors = _base_extractors({
            FieldType.LANGUAGES: [_mock_extractor(["English", "Spanish"])],
        })
        coord = ResumeExtractor(extractors)

        result = coord.extract("Resume text")

        assert result.languages == ["English", "Spanish"]

    def test_awards_extracted(self):
        extractors = _base_extractors({
            FieldType.AWARDS: [_mock_extractor(["Best Engineer 2023"])],
        })
        coord = ResumeExtractor(extractors)

        result = coord.extract("Resume text")

        assert result.awards == ["Best Engineer 2023"]

    def test_list_fields_default_to_empty_list_when_missing(self):
        coord = ResumeExtractor(_base_extractors())

        result = coord.extract("Resume text")

        assert result.interests == []
        assert result.languages == []
        assert result.awards == []


# ---------------------------------------------------------------------------
# Experience analytics computation
# ---------------------------------------------------------------------------

class TestResumeExtractorAnalytics:
    """Test analytics computation from work experience."""

    def test_analytics_computed_when_work_experience_present(self):
        """Analytics are computed when work_experience is non-empty."""
        entry = WorkExperienceEntry(
            company="BigCo",
            title="Senior Engineer",
            duration_months=36,
            skills_used=["Python"],
        )
        extractors = _base_extractors({
            FieldType.WORK_EXPERIENCE: [_mock_extractor([entry])],
        })
        coord = ResumeExtractor(extractors)

        result = coord.extract("Resume text")

        assert result.experience_analytics is not None
        assert result.experience_analytics.total_years == 3.0
        assert result.experience_analytics.career_level == "Senior"

    def test_analytics_none_when_no_work_experience(self):
        """Analytics are None when work_experience is empty."""
        coord = ResumeExtractor(_base_extractors())

        result = coord.extract("Resume text")

        assert result.experience_analytics is None

    def test_analytics_none_when_work_experience_fails(self):
        """Analytics are None when work experience extraction fails."""
        extractors = _base_extractors({
            FieldType.WORK_EXPERIENCE: [_failing_extractor()],
        })
        coord = ResumeExtractor(extractors)

        result = coord.extract("Resume text")

        assert result.experience_analytics is None

    def test_custom_analytics_extractor_used(self):
        """Custom ExperienceAnalyticsExtractor is called when provided."""
        entry = WorkExperienceEntry(company="Corp", title="Dev", duration_months=12)
        mock_analytics = Mock(spec=ExperienceAnalyticsExtractor)
        mock_analytics.compute.return_value = ExperienceAnalytics(
            total_years=1.0,
            career_level="Mid",
        )
        extractors = _base_extractors({
            FieldType.WORK_EXPERIENCE: [_mock_extractor([entry])],
        })
        coord = ResumeExtractor(extractors, analytics_extractor=mock_analytics)

        result = coord.extract("Resume text")

        mock_analytics.compute.assert_called_once_with([entry])
        assert result.experience_analytics.total_years == 1.0

    def test_analytics_failure_does_not_abort_extraction(self):
        """If analytics computation raises, other fields are still returned."""
        entry = WorkExperienceEntry(company="Corp", title="Dev", duration_months=12)
        mock_analytics = Mock(spec=ExperienceAnalyticsExtractor)
        mock_analytics.compute.side_effect = RuntimeError("analytics error")
        extractors = _base_extractors({
            FieldType.WORK_EXPERIENCE: [_mock_extractor([entry])],
        })
        coord = ResumeExtractor(extractors, analytics_extractor=mock_analytics)

        result = coord.extract("Resume text")

        assert result.experience_analytics is None
        assert result.name == "John Doe"  # other fields unaffected


# ---------------------------------------------------------------------------
# Fallback behaviour
# ---------------------------------------------------------------------------

class TestResumeExtractorFallbackBehaviour:
    """Test extractor chain fallback for new field types."""

    def test_second_extractor_tried_when_first_fails(self):
        """When the first extractor in a chain fails, the second is tried."""
        extractors = _base_extractors({
            FieldType.PHONE: [
                _failing_extractor("first failed"),
                _mock_extractor("+1-555-000-1234"),
            ],
        })
        coord = ResumeExtractor(extractors)

        result = coord.extract("Resume text")

        assert result.contact.phone == "+1-555-000-1234"

    def test_all_extractors_fail_returns_none_for_scalar(self):
        """All extractors failing for a scalar field returns None."""
        extractors = _base_extractors({
            FieldType.LOCATION: [
                _failing_extractor(),
                _failing_extractor(),
            ],
        })
        coord = ResumeExtractor(extractors)

        result = coord.extract("Resume text")

        assert result.contact.location is None

    def test_all_extractors_fail_returns_empty_list_for_list_field(self):
        """All extractors failing for a list field returns []."""
        extractors = _base_extractors({
            FieldType.INTERESTS: [_failing_extractor(), _failing_extractor()],
        })
        coord = ResumeExtractor(extractors)

        result = coord.extract("Resume text")

        assert result.interests == []

    def test_empty_extractor_result_falls_through_to_next(self):
        """An extractor returning empty string falls through to the next."""
        extractors = _base_extractors({
            FieldType.LOCATION: [
                _mock_extractor(""),       # empty → skip
                _mock_extractor("London"), # this should win
            ],
        })
        coord = ResumeExtractor(extractors)

        result = coord.extract("Resume text")

        assert result.contact.location == "London"


# ---------------------------------------------------------------------------
# Result structure
# ---------------------------------------------------------------------------

class TestResumeExtractorResultStructure:
    """Verify the returned ResumeData has the expected shape."""

    def test_result_is_resume_data(self):
        coord = ResumeExtractor(_base_extractors())
        result = coord.extract("Some resume text")

        assert isinstance(result, ResumeData)

    def test_required_fields_populated(self):
        coord = ResumeExtractor(_base_extractors())
        result = coord.extract("Some resume text")

        assert result.name == "John Doe"
        assert result.email == "john@example.com"
        assert result.skills == ["Python", "SQL"]

    def test_contact_always_present_as_object(self):
        """contact is always a ContactInfo object, never None."""
        coord = ResumeExtractor(_base_extractors())
        result = coord.extract("Resume text")

        assert result.contact is not None
        assert isinstance(result.contact, ContactInfo)
