"""Tests for factory with new field types added in the comprehensive expansion."""

import pytest
from unittest.mock import patch, Mock

from extractors.factory import create_extractor, _create_field_spec, SUPPORTED_STRATEGIES
from extractors.phone_extractor import PhoneExtractor
from extractors.location_extractor import LocationExtractor
from extractors.urls_extractor import UrlsExtractor
from extractors.summary_extractor import SummaryExtractor
from extractors.list_field_extractor import ListFieldExtractor
from extractors.work_experience_extractor import WorkExperienceExtractor
from extractors.education_extractor import EducationExtractor
from extractors.certifications_extractor import CertificationsExtractor
from extractors.projects_extractor import ProjectsExtractor
from extractors.volunteer_extractor import VolunteerExtractor
from extractors.publications_extractor import PublicationsExtractor
from interfaces import FieldType, StrategyType, ExtractionStrategy
from exceptions import InvalidStrategyConfigError


class TestFactoryPhoneField:
    """Factory tests for PHONE field type."""

    @patch("extractors.factory.RegexExtractionStrategy")
    def test_create_phone_extractor_with_regex(self, mock_regex_class):
        mock_regex_class.return_value = Mock(spec=ExtractionStrategy)
        extractor = create_extractor(FieldType.PHONE, StrategyType.REGEX)

        assert isinstance(extractor, PhoneExtractor)
        mock_regex_class.assert_called_once()

    @patch("extractors.factory.LLMExtractionStrategy")
    def test_create_phone_extractor_with_llm(self, mock_llm_class):
        mock_llm_class.return_value = Mock(spec=ExtractionStrategy)
        extractor = create_extractor(FieldType.PHONE, StrategyType.LLM)

        assert isinstance(extractor, PhoneExtractor)

    def test_phone_field_spec_has_regex_patterns(self):
        spec = _create_field_spec(FieldType.PHONE)

        assert spec.field_type == FieldType.PHONE
        assert spec.regex_patterns is not None
        assert len(spec.regex_patterns) > 0

    def test_phone_supported_strategies(self):
        strategies = SUPPORTED_STRATEGIES[FieldType.PHONE]

        assert StrategyType.REGEX in strategies
        assert StrategyType.LLM in strategies


class TestFactoryLocationField:
    """Factory tests for LOCATION field type."""

    @patch("extractors.factory.LLMExtractionStrategy")
    def test_create_location_extractor_with_llm(self, mock_llm_class):
        mock_llm_class.return_value = Mock(spec=ExtractionStrategy)
        extractor = create_extractor(FieldType.LOCATION, StrategyType.LLM)

        assert isinstance(extractor, LocationExtractor)

    @patch("extractors.factory.NERExtractionStrategy")
    def test_create_location_extractor_with_ner(self, mock_ner_class):
        mock_ner_class.return_value = Mock(spec=ExtractionStrategy)
        extractor = create_extractor(FieldType.LOCATION, StrategyType.NER)

        assert isinstance(extractor, LocationExtractor)

    def test_location_supported_strategies(self):
        strategies = SUPPORTED_STRATEGIES[FieldType.LOCATION]

        assert StrategyType.NER in strategies
        assert StrategyType.LLM in strategies


class TestFactoryUrlFields:
    """Factory tests for URL field types (LinkedIn, GitHub, Portfolio, Other)."""

    @patch("extractors.factory.RegexExtractionStrategy")
    def test_create_linkedin_url_extractor(self, mock_regex_class):
        mock_regex_class.return_value = Mock(spec=ExtractionStrategy)
        extractor = create_extractor(FieldType.LINKEDIN_URL, StrategyType.REGEX)

        assert isinstance(extractor, UrlsExtractor)
        assert extractor.field_type == FieldType.LINKEDIN_URL

    @patch("extractors.factory.RegexExtractionStrategy")
    def test_create_github_url_extractor(self, mock_regex_class):
        mock_regex_class.return_value = Mock(spec=ExtractionStrategy)
        extractor = create_extractor(FieldType.GITHUB_URL, StrategyType.REGEX)

        assert isinstance(extractor, UrlsExtractor)
        assert extractor.field_type == FieldType.GITHUB_URL

    @patch("extractors.factory.RegexExtractionStrategy")
    def test_create_portfolio_url_extractor(self, mock_regex_class):
        mock_regex_class.return_value = Mock(spec=ExtractionStrategy)
        extractor = create_extractor(FieldType.PORTFOLIO_URL, StrategyType.REGEX)

        assert isinstance(extractor, UrlsExtractor)
        assert extractor.field_type == FieldType.PORTFOLIO_URL

    @patch("extractors.factory.RegexExtractionStrategy")
    def test_create_other_urls_extractor(self, mock_regex_class):
        mock_regex_class.return_value = Mock(spec=ExtractionStrategy)
        extractor = create_extractor(FieldType.OTHER_URLS, StrategyType.REGEX)

        assert isinstance(extractor, UrlsExtractor)
        assert extractor.field_type == FieldType.OTHER_URLS

    def test_url_fields_have_regex_patterns(self):
        for field_type in (
            FieldType.LINKEDIN_URL,
            FieldType.GITHUB_URL,
            FieldType.PORTFOLIO_URL,
            FieldType.OTHER_URLS,
        ):
            spec = _create_field_spec(field_type)
            assert spec.regex_patterns is not None, f"Missing patterns for {field_type}"


class TestFactorySummaryField:
    """Factory tests for SUMMARY field type."""

    @patch("extractors.factory.LLMExtractionStrategy")
    def test_create_summary_extractor_with_llm(self, mock_llm_class):
        mock_llm_class.return_value = Mock(spec=ExtractionStrategy)
        extractor = create_extractor(FieldType.SUMMARY, StrategyType.LLM)

        assert isinstance(extractor, SummaryExtractor)

    def test_summary_supported_strategies(self):
        assert StrategyType.LLM in SUPPORTED_STRATEGIES[FieldType.SUMMARY]


class TestFactoryListFields:
    """Factory tests for list field types (INTERESTS, LANGUAGES, AWARDS)."""

    @patch("extractors.factory.LLMExtractionStrategy")
    def test_create_interests_extractor(self, mock_llm_class):
        mock_llm_class.return_value = Mock(spec=ExtractionStrategy)
        extractor = create_extractor(FieldType.INTERESTS, StrategyType.LLM)

        assert isinstance(extractor, ListFieldExtractor)
        assert extractor.field_type == FieldType.INTERESTS

    @patch("extractors.factory.LLMExtractionStrategy")
    def test_create_languages_extractor(self, mock_llm_class):
        mock_llm_class.return_value = Mock(spec=ExtractionStrategy)
        extractor = create_extractor(FieldType.LANGUAGES, StrategyType.LLM)

        assert isinstance(extractor, ListFieldExtractor)
        assert extractor.field_type == FieldType.LANGUAGES

    @patch("extractors.factory.LLMExtractionStrategy")
    def test_create_awards_extractor(self, mock_llm_class):
        mock_llm_class.return_value = Mock(spec=ExtractionStrategy)
        extractor = create_extractor(FieldType.AWARDS, StrategyType.LLM)

        assert isinstance(extractor, ListFieldExtractor)
        assert extractor.field_type == FieldType.AWARDS


class TestFactoryStructuredFields:
    """Factory tests for structured section field types."""

    @patch("extractors.factory.LLMExtractionStrategy")
    def test_create_work_experience_extractor(self, mock_llm_class):
        mock_llm_class.return_value = Mock(spec=ExtractionStrategy)
        extractor = create_extractor(FieldType.WORK_EXPERIENCE, StrategyType.LLM)

        assert isinstance(extractor, WorkExperienceExtractor)

    @patch("extractors.factory.LLMExtractionStrategy")
    def test_create_education_extractor(self, mock_llm_class):
        mock_llm_class.return_value = Mock(spec=ExtractionStrategy)
        extractor = create_extractor(FieldType.EDUCATION, StrategyType.LLM)

        assert isinstance(extractor, EducationExtractor)

    @patch("extractors.factory.LLMExtractionStrategy")
    def test_create_certifications_extractor(self, mock_llm_class):
        mock_llm_class.return_value = Mock(spec=ExtractionStrategy)
        extractor = create_extractor(FieldType.CERTIFICATIONS, StrategyType.LLM)

        assert isinstance(extractor, CertificationsExtractor)

    @patch("extractors.factory.LLMExtractionStrategy")
    def test_create_projects_extractor(self, mock_llm_class):
        mock_llm_class.return_value = Mock(spec=ExtractionStrategy)
        extractor = create_extractor(FieldType.PROJECTS, StrategyType.LLM)

        assert isinstance(extractor, ProjectsExtractor)

    @patch("extractors.factory.LLMExtractionStrategy")
    def test_create_volunteer_extractor(self, mock_llm_class):
        mock_llm_class.return_value = Mock(spec=ExtractionStrategy)
        extractor = create_extractor(FieldType.VOLUNTEER_EXPERIENCE, StrategyType.LLM)

        assert isinstance(extractor, VolunteerExtractor)

    @patch("extractors.factory.LLMExtractionStrategy")
    def test_create_publications_extractor(self, mock_llm_class):
        mock_llm_class.return_value = Mock(spec=ExtractionStrategy)
        extractor = create_extractor(FieldType.PUBLICATIONS, StrategyType.LLM)

        assert isinstance(extractor, PublicationsExtractor)

    def test_structured_fields_have_is_structured_true(self):
        """Structured field specs must have is_structured=True."""
        structured_fields = [
            FieldType.WORK_EXPERIENCE,
            FieldType.EDUCATION,
            FieldType.CERTIFICATIONS,
            FieldType.PROJECTS,
            FieldType.VOLUNTEER_EXPERIENCE,
            FieldType.PUBLICATIONS,
        ]
        for field_type in structured_fields:
            spec = _create_field_spec(field_type)
            assert spec.is_structured is True, f"{field_type} missing is_structured=True"


class TestFactoryAllFieldTypesCovered:
    """Ensure every FieldType has an entry in SUPPORTED_STRATEGIES."""

    def test_all_field_types_have_supported_strategies(self):
        for field_type in FieldType:
            assert field_type in SUPPORTED_STRATEGIES, (
                f"FieldType.{field_type.name} is missing from SUPPORTED_STRATEGIES"
            )
