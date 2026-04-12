"""Tests for SkillsExtractor."""

import pytest
from unittest.mock import Mock

from extractors.skills_extractor import SkillsExtractor
from interfaces import ExtractionStrategy
from exceptions import FieldExtractionError


class TestSkillsExtractor:
    """Test cases for SkillsExtractor."""

    def test_extract_success(self):
        """Test successful skills extraction."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["Python", "Java", "SQL"]
        extractor = SkillsExtractor(mock_strategy)
        text = "Skills: Python, Java, SQL"

        # Act
        result = extractor.extract(text)

        # Assert
        assert result == ["Python", "Java", "SQL"]
        mock_strategy.extract.assert_called_once_with(text)

    def test_extract_single_skill(self):
        """Test extraction with single skill."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["Python"]
        extractor = SkillsExtractor(mock_strategy)

        # Act
        result = extractor.extract("Only Python")

        # Assert
        assert result == ["Python"]

    def test_extract_many_skills(self):
        """Test extraction with many skills."""
        # Arrange
        skills_list = [
            "Python",
            "Java",
            "JavaScript",
            "SQL",
            "Docker",
            "Kubernetes",
            "AWS",
            "Machine Learning",
        ]
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = skills_list
        extractor = SkillsExtractor(mock_strategy)

        # Act
        result = extractor.extract("Long resume with many skills")

        # Assert
        assert result == skills_list
        assert len(result) == 8

    def test_extract_no_skills_found(self):
        """Test extraction when no skills are found."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = []
        extractor = SkillsExtractor(mock_strategy)

        # Act & Assert
        with pytest.raises(FieldExtractionError, match="Skills extraction failed"):
            extractor.extract("Text without skills")

    def test_extract_with_whitespace(self):
        """Test extraction with leading/trailing whitespace."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["React", "Node.js"]
        extractor = SkillsExtractor(mock_strategy)

        # Act
        result = extractor.extract("   Resume text with skills   ")

        # Assert
        assert result == ["React", "Node.js"]
        mock_strategy.extract.assert_called_once_with("Resume text with skills")

    def test_extract_strategy_raises_exception(self):
        """Test when strategy raises an exception."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.side_effect = ValueError("Strategy failed")
        extractor = SkillsExtractor(mock_strategy)

        # Act & Assert
        with pytest.raises(FieldExtractionError, match="Skills extraction failed"):
            extractor.extract("Some text")

    def test_validate_input_empty_string(self):
        """Test validation with empty string."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)
        extractor = SkillsExtractor(mock_strategy)

        # Act & Assert
        with pytest.raises(
            FieldExtractionError,
            match="Input text must be at least 2 characters long after stripping",
        ):
            extractor.extract("")

    def test_validate_input_single_character(self):
        """Test validation with single character."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)
        extractor = SkillsExtractor(mock_strategy)

        # Act & Assert
        with pytest.raises(
            FieldExtractionError,
            match="Input text must be at least 2 characters long after stripping",
        ):
            extractor.extract("A")

    def test_validate_input_whitespace_only(self):
        """Test validation with whitespace-only string."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)
        extractor = SkillsExtractor(mock_strategy)

        # Act & Assert
        with pytest.raises(
            FieldExtractionError,
            match="Input text must be at least 2 characters long after stripping",
        ):
            extractor.extract("   ")

    def test_validate_input_exactly_two_characters(self):
        """Test validation with exactly 2 characters (edge case - should pass)."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["Go"]
        extractor = SkillsExtractor(mock_strategy)

        # Act
        result = extractor.extract("Go")

        # Assert
        assert result == ["Go"]

    def test_extract_preserves_order(self):
        """Test that extraction preserves the order of skills."""
        # Arrange
        ordered_skills = ["First", "Second", "Third", "Fourth"]
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ordered_skills
        extractor = SkillsExtractor(mock_strategy)

        # Act
        result = extractor.extract("Skills in order")

        # Assert
        assert result == ordered_skills

    def test_extract_with_duplicate_skills(self):
        """Test extraction when strategy returns duplicate skills."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["Python", "Java", "Python", "SQL"]
        extractor = SkillsExtractor(mock_strategy)

        # Act
        result = extractor.extract("Skills with duplicates")

        # Assert
        # Extractor doesn't deduplicate - that's the strategy's job
        assert result == ["Python", "Java", "Python", "SQL"]

    def test_extract_with_special_characters(self):
        """Test extraction with skills containing special characters."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)
        mock_strategy.extract.return_value = ["C++", "C#", "Node.js", "Vue.js"]
        extractor = SkillsExtractor(mock_strategy)

        # Act
        result = extractor.extract("Skills: C++, C#, Node.js, Vue.js")

        # Assert
        assert result == ["C++", "C#", "Node.js", "Vue.js"]

    def test_extractor_initialization(self):
        """Test that extractor initializes correctly."""
        # Arrange
        mock_strategy = Mock(spec=ExtractionStrategy)

        # Act
        extractor = SkillsExtractor(mock_strategy)

        # Assert
        assert extractor.extraction_strategy == mock_strategy
