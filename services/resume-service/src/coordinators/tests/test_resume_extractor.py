"""Tests for ResumeExtractor coordinator."""

import pytest
from unittest.mock import Mock

from coordinators.resume_extractor import ResumeExtractor
from interfaces import FieldExtractor, FieldType
from models import ResumeData


class TestResumeExtractorInitialization:
    """Test cases for ResumeExtractor initialization."""

    def test_initialization_with_valid_extractors(self):
        """Test successful initialization with valid extractors dict."""
        # Arrange
        name_extractor1 = Mock(spec=FieldExtractor)
        name_extractor2 = Mock(spec=FieldExtractor)
        email_extractor = Mock(spec=FieldExtractor)
        skills_extractor = Mock(spec=FieldExtractor)

        extractors = {
            FieldType.NAME: [name_extractor1, name_extractor2],
            FieldType.EMAIL: [email_extractor],
            FieldType.SKILLS: [skills_extractor],
        }

        # Act
        extractor = ResumeExtractor(extractors)

        # Assert
        assert extractor.extractors == extractors
        assert len(extractor.extractors[FieldType.NAME]) == 2
        assert len(extractor.extractors[FieldType.EMAIL]) == 1
        assert len(extractor.extractors[FieldType.SKILLS]) == 1

    def test_initialization_with_none_extractors_dict_raises_error(self):
        """Test that None extractors dict raises ValueError."""
        # Act & Assert
        with pytest.raises(
            ValueError, match="extractors dictionary cannot be None or empty"
        ):
            ResumeExtractor(None)  # type: ignore

    def test_initialization_with_empty_extractors_dict_raises_error(self):
        """Test that empty extractors dict raises ValueError."""
        # Act & Assert
        with pytest.raises(
            ValueError, match="extractors dictionary cannot be None or empty"
        ):
            ResumeExtractor({})

    def test_initialization_with_missing_field_type_raises_error(self):
        """Test that missing required field type raises ValueError."""
        # Arrange - only provide NAME, missing EMAIL and SKILLS
        name_extractor = Mock(spec=FieldExtractor)
        extractors = {
            FieldType.NAME: [name_extractor],
        }

        # Act & Assert
        with pytest.raises(ValueError, match="Missing required field types"):
            ResumeExtractor(extractors)


class TestResumeExtractorExtraction:
    """Test cases for ResumeExtractor extract method."""

    def test_extract_successful(self):
        """Test successful extraction of all fields using first extractor."""
        # Arrange
        name_extractor = Mock(spec=FieldExtractor)
        name_extractor.extract.return_value = "John Doe"

        email_extractor = Mock(spec=FieldExtractor)
        email_extractor.extract.return_value = "john.doe@example.com"

        skills_extractor = Mock(spec=FieldExtractor)
        skills_extractor.extract.return_value = ["Python", "Java", "SQL"]

        extractors = {
            FieldType.NAME: [name_extractor],
            FieldType.EMAIL: [email_extractor],
            FieldType.SKILLS: [skills_extractor],
        }
        extractor = ResumeExtractor(extractors)
        text = "Resume text with all information"

        # Act
        result = extractor.extract(text)

        # Assert
        assert isinstance(result, ResumeData)
        assert result.name == "John Doe"
        assert result.email == "john.doe@example.com"
        assert result.skills == ["Python", "Java", "SQL"]

        # Verify all extractors were called
        name_extractor.extract.assert_called_once_with(text)
        email_extractor.extract.assert_called_once_with(text)
        skills_extractor.extract.assert_called_once_with(text)

    def test_extract_with_empty_skills(self):
        """Test extraction with empty skills list."""
        # Arrange
        name_extractor = Mock(spec=FieldExtractor)
        name_extractor.extract.return_value = "Jane Smith"

        email_extractor = Mock(spec=FieldExtractor)
        email_extractor.extract.return_value = "jane@example.com"

        skills_extractor = Mock(spec=FieldExtractor)
        skills_extractor.extract.return_value = []

        extractors = {
            FieldType.NAME: [name_extractor],
            FieldType.EMAIL: [email_extractor],
            FieldType.SKILLS: [skills_extractor],
        }
        extractor = ResumeExtractor(extractors)

        # Act
        result = extractor.extract("Resume text")

        # Assert
        assert result.name == "Jane Smith"
        assert result.email == "jane@example.com"
        assert result.skills == []

    def test_extract_with_single_skill(self):
        """Test extraction with a single skill."""
        # Arrange
        name_extractor = Mock(spec=FieldExtractor)
        name_extractor.extract.return_value = "Bob Johnson"

        email_extractor = Mock(spec=FieldExtractor)
        email_extractor.extract.return_value = "bob@example.com"

        skills_extractor = Mock(spec=FieldExtractor)
        skills_extractor.extract.return_value = ["Python"]

        extractors = {
            FieldType.NAME: [name_extractor],
            FieldType.EMAIL: [email_extractor],
            FieldType.SKILLS: [skills_extractor],
        }
        extractor = ResumeExtractor(extractors)

        # Act
        result = extractor.extract("Resume text")

        # Assert
        assert result.skills is not None
        assert len(result.skills) == 1
        assert result.skills[0] == "Python"

    def test_extract_with_many_skills(self):
        """Test extraction with many skills."""
        # Arrange
        name_extractor = Mock(spec=FieldExtractor)
        name_extractor.extract.return_value = "Alice Williams"

        email_extractor = Mock(spec=FieldExtractor)
        email_extractor.extract.return_value = "alice@example.com"

        many_skills = [
            "Python",
            "Java",
            "JavaScript",
            "SQL",
            "Docker",
            "Kubernetes",
            "AWS",
            "Machine Learning",
        ]
        skills_extractor = Mock(spec=FieldExtractor)
        skills_extractor.extract.return_value = many_skills

        extractors = {
            FieldType.NAME: [name_extractor],
            FieldType.EMAIL: [email_extractor],
            FieldType.SKILLS: [skills_extractor],
        }
        extractor = ResumeExtractor(extractors)

        # Act
        result = extractor.extract("Resume text")

        # Assert
        assert result.skills is not None
        assert len(result.skills) == 8
        assert result.skills == many_skills

    def test_extract_with_fallback_to_second_extractor(self):
        """Test that second extractor is tried when first fails."""
        # Arrange
        name_extractor1 = Mock(spec=FieldExtractor)
        name_extractor1.extract.side_effect = Exception("First extractor failed")

        name_extractor2 = Mock(spec=FieldExtractor)
        name_extractor2.extract.return_value = "John Doe"

        email_extractor = Mock(spec=FieldExtractor)
        email_extractor.extract.return_value = "john@example.com"

        skills_extractor = Mock(spec=FieldExtractor)
        skills_extractor.extract.return_value = ["Python"]

        extractors = {
            FieldType.NAME: [name_extractor1, name_extractor2],
            FieldType.EMAIL: [email_extractor],
            FieldType.SKILLS: [skills_extractor],
        }
        extractor = ResumeExtractor(extractors)

        # Act
        result = extractor.extract("Resume text")

        # Assert - second name extractor should succeed
        assert result.name == "John Doe"
        name_extractor1.extract.assert_called_once()
        name_extractor2.extract.assert_called_once()

    def test_extract_allows_none_when_all_extractors_fail(self):
        """Test that None is returned when all extractors fail."""
        # Arrange
        name_extractor1 = Mock(spec=FieldExtractor)
        name_extractor1.extract.side_effect = Exception("Failed")

        name_extractor2 = Mock(spec=FieldExtractor)
        name_extractor2.extract.side_effect = Exception("Failed")

        email_extractor = Mock(spec=FieldExtractor)
        email_extractor.extract.return_value = "john@example.com"

        skills_extractor = Mock(spec=FieldExtractor)
        skills_extractor.extract.return_value = ["Python"]

        extractors = {
            FieldType.NAME: [name_extractor1, name_extractor2],
            FieldType.EMAIL: [email_extractor],
            FieldType.SKILLS: [skills_extractor],
        }
        extractor = ResumeExtractor(extractors)

        # Act
        result = extractor.extract("Resume text")

        # Assert - name should be None since all extractors failed
        assert result.name is None
        assert result.email == "john@example.com"
        assert result.skills == ["Python"]


class TestResumeExtractorValidation:
    """Test cases for ResumeExtractor input validation."""

    def test_extract_with_empty_text_raises_error(self):
        """Test that empty text raises ValueError."""
        # Arrange
        name_extractor = Mock(spec=FieldExtractor)
        email_extractor = Mock(spec=FieldExtractor)
        skills_extractor = Mock(spec=FieldExtractor)

        extractors = {
            FieldType.NAME: [name_extractor],
            FieldType.EMAIL: [email_extractor],
            FieldType.SKILLS: [skills_extractor],
        }
        extractor = ResumeExtractor(extractors)

        # Act & Assert
        with pytest.raises(ValueError, match="Resume text cannot be empty"):
            extractor.extract("")

    def test_extract_with_whitespace_only_raises_error(self):
        """Test that whitespace-only text raises ValueError."""
        # Arrange
        name_extractor = Mock(spec=FieldExtractor)
        email_extractor = Mock(spec=FieldExtractor)
        skills_extractor = Mock(spec=FieldExtractor)

        extractors = {
            FieldType.NAME: [name_extractor],
            FieldType.EMAIL: [email_extractor],
            FieldType.SKILLS: [skills_extractor],
        }
        extractor = ResumeExtractor(extractors)

        # Act & Assert
        with pytest.raises(ValueError, match="Resume text cannot be empty"):
            extractor.extract("   ")


class TestResumeExtractorErrorHandling:
    """Test cases for ResumeExtractor error handling - now logs errors but returns None."""

    def test_name_extraction_failure_logs_and_returns_none(self):
        """Test that name extraction failure is logged but returns None."""
        # Arrange
        name_extractor = Mock(spec=FieldExtractor)
        name_extractor.extract.side_effect = Exception("Name extraction failed")

        email_extractor = Mock(spec=FieldExtractor)
        email_extractor.extract.return_value = "john@example.com"

        skills_extractor = Mock(spec=FieldExtractor)
        skills_extractor.extract.return_value = ["Python"]

        extractors = {
            FieldType.NAME: [name_extractor],
            FieldType.EMAIL: [email_extractor],
            FieldType.SKILLS: [skills_extractor],
        }
        extractor = ResumeExtractor(extractors)

        # Act
        result = extractor.extract("Resume text")

        # Assert - name is None, but other fields extracted
        assert result.name is None
        assert result.email == "john@example.com"
        assert result.skills == ["Python"]

    def test_email_extraction_failure_logs_and_returns_none(self):
        """Test that email extraction failure is logged but returns None."""
        # Arrange
        name_extractor = Mock(spec=FieldExtractor)
        name_extractor.extract.return_value = "John Doe"

        email_extractor = Mock(spec=FieldExtractor)
        email_extractor.extract.side_effect = Exception("Email extraction failed")

        skills_extractor = Mock(spec=FieldExtractor)
        skills_extractor.extract.return_value = ["Python"]

        extractors = {
            FieldType.NAME: [name_extractor],
            FieldType.EMAIL: [email_extractor],
            FieldType.SKILLS: [skills_extractor],
        }
        extractor = ResumeExtractor(extractors)

        # Act
        result = extractor.extract("Resume text")

        # Assert - email is None, but other fields extracted
        assert result.name == "John Doe"
        assert result.email is None
        assert result.skills == ["Python"]

    def test_skills_extraction_failure_logs_and_returns_empty_list(self):
        """Test that skills extraction failure is logged but returns empty list."""
        # Arrange
        name_extractor = Mock(spec=FieldExtractor)
        name_extractor.extract.return_value = "John Doe"

        email_extractor = Mock(spec=FieldExtractor)
        email_extractor.extract.return_value = "john@example.com"

        skills_extractor = Mock(spec=FieldExtractor)
        skills_extractor.extract.side_effect = Exception("Skills extraction failed")

        extractors = {
            FieldType.NAME: [name_extractor],
            FieldType.EMAIL: [email_extractor],
            FieldType.SKILLS: [skills_extractor],
        }
        extractor = ResumeExtractor(extractors)

        # Act
        result = extractor.extract("Resume text")

        # Assert - skills is empty list (not None), but other fields extracted
        assert result.name == "John Doe"
        assert result.email == "john@example.com"
        assert result.skills == []  # Empty list when all skills extractors fail

    def test_all_extractions_continue_despite_earlier_failures(self):
        """Test that all fields are attempted even if earlier ones fail."""
        # Arrange
        name_extractor = Mock(spec=FieldExtractor)
        name_extractor.extract.side_effect = Exception("Name extraction failed")

        email_extractor = Mock(spec=FieldExtractor)
        email_extractor.extract.return_value = "john@example.com"

        skills_extractor = Mock(spec=FieldExtractor)
        skills_extractor.extract.return_value = ["Python"]

        extractors = {
            FieldType.NAME: [name_extractor],
            FieldType.EMAIL: [email_extractor],
            FieldType.SKILLS: [skills_extractor],
        }
        extractor = ResumeExtractor(extractors)

        # Act
        result = extractor.extract("Resume text")

        # Assert - all extractors called, successful ones return values
        name_extractor.extract.assert_called_once()
        email_extractor.extract.assert_called_once()
        skills_extractor.extract.assert_called_once()

        assert result.name is None
        assert result.email == "john@example.com"
        assert result.skills == ["Python"]
