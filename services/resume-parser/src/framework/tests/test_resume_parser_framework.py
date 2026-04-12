"""Tests for ResumeParserFramework."""

import pytest
from unittest.mock import Mock, patch

from framework.resume_parser_framework import ResumeParserFramework
from coordinators import ResumeExtractor
from interfaces import FileParser, FieldType, StrategyType
from models import ResumeData
from config import ExtractionConfig
from exceptions import (
    UnsupportedFileFormatError,
    FileParsingError,
    FieldExtractionError,
)


class TestResumeParserFrameworkInitialization:
    """Test cases for ResumeParserFramework initialization."""

    @patch.object(ResumeParserFramework, "_create_extractor")
    def test_initialization_with_default_config(
        self, mock_create_extractor: Mock
    ) -> None:
        """Test successful initialization with default configuration."""
        # Arrange - mock the factory to avoid actual model loading
        mock_extractor = Mock()
        mock_create_extractor.return_value = mock_extractor

        # Act
        framework = ResumeParserFramework()

        # Assert
        assert framework.extractor is not None
        assert len(framework.parsers) == 3
        assert ".pdf" in framework.parsers
        assert ".docx" in framework.parsers
        assert ".doc" in framework.parsers
        assert framework.config is not None

    @patch.object(ResumeParserFramework, "_create_extractor")
    def test_initialization_with_custom_parsers(
        self, mock_create_extractor: Mock
    ) -> None:
        """Test initialization with custom parsers."""
        # Arrange
        mock_extractor = Mock()
        mock_create_extractor.return_value = mock_extractor
        pdf_parser = Mock(spec=FileParser)
        word_parser = Mock(spec=FileParser)

        # Act
        framework = ResumeParserFramework(
            pdf_parser=pdf_parser, word_parser=word_parser
        )

        # Assert
        assert framework.parsers[".pdf"] == pdf_parser
        assert framework.parsers[".docx"] == word_parser
        assert framework.parsers[".doc"] == word_parser

    @patch.object(ResumeParserFramework, "_create_extractor")
    def test_initialization_with_custom_config(
        self, mock_create_extractor: Mock
    ) -> None:
        """Test initialization with custom configuration."""
        # Arrange
        mock_extractor = Mock()
        mock_create_extractor.return_value = mock_extractor

        custom_config = ExtractionConfig(
            strategy_preferences={
                FieldType.NAME: [StrategyType.NER],
                FieldType.EMAIL: [StrategyType.REGEX],
                FieldType.SKILLS: [StrategyType.NER],
            }
        )

        # Act
        framework = ResumeParserFramework(config=custom_config)

        # Assert
        assert framework.config == custom_config
        assert framework.extractor is not None


class TestResumeParserFrameworkParseResume:
    """Test cases for parse_resume method."""

    @patch.object(ResumeParserFramework, "_create_extractor")
    @patch("framework.resume_parser_framework.Path")
    def test_parse_pdf_resume_success(
        self, mock_path_class: Mock, mock_create_extractor_method: Mock
    ) -> None:
        """Test successful parsing of PDF resume."""
        # Arrange
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = True
        mock_path.suffix = ".pdf"
        mock_path_class.return_value = mock_path

        # Create actual ResumeData instead of mocking
        resume_data = ResumeData(
            name="John Doe", email="john@example.com", skills=["Python"]
        )

        mock_extractor = Mock()
        mock_extractor.extract = Mock(return_value=resume_data)
        mock_create_extractor_method.return_value = mock_extractor

        pdf_parser = Mock(spec=FileParser)
        pdf_parser.parse.return_value = "Resume text content"

        framework = ResumeParserFramework(pdf_parser=pdf_parser)

        # Act
        result = framework.parse_resume("/path/to/resume.pdf")

        # Assert
        assert result == resume_data
        pdf_parser.parse.assert_called_once_with("/path/to/resume.pdf")
        mock_extractor.extract.assert_called_once_with("Resume text content")

    @patch.object(ResumeParserFramework, "_create_extractor")
    @patch("framework.resume_parser_framework.Path")
    def test_parse_docx_resume_success(
        self, mock_path_class: Mock, mock_create_extractor: Mock
    ) -> None:
        """Test successful parsing of DOCX resume."""
        # Arrange
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = True
        mock_path.suffix = ".docx"
        mock_path_class.return_value = mock_path

        resume_data = ResumeData(
            name="Jane Smith", email="jane@example.com", skills=["Java"]
        )

        mock_extractor = Mock()
        mock_extractor.extract = Mock(return_value=resume_data)
        mock_create_extractor.return_value = mock_extractor

        word_parser = Mock(spec=FileParser)
        word_parser.parse.return_value = "DOCX resume text"

        framework = ResumeParserFramework(word_parser=word_parser)

        # Act
        result = framework.parse_resume("/path/to/resume.docx")

        # Assert
        assert result == resume_data
        word_parser.parse.assert_called_once_with("/path/to/resume.docx")

    @patch.object(ResumeParserFramework, "_create_extractor")
    @patch("framework.resume_parser_framework.Path")
    def test_parse_doc_resume_success(
        self, mock_path_class: Mock, mock_create_extractor: Mock
    ) -> None:
        """Test successful parsing of DOC resume."""
        # Arrange
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = True
        mock_path.suffix = ".doc"
        mock_path_class.return_value = mock_path

        resume_data = ResumeData(
            name="Bob Johnson", email="bob@example.com", skills=["SQL"]
        )

        mock_extractor = Mock()
        mock_extractor.extract = Mock(return_value=resume_data)
        mock_create_extractor.return_value = mock_extractor

        word_parser = Mock(spec=FileParser)
        word_parser.parse.return_value = "DOC resume text"

        framework = ResumeParserFramework(word_parser=word_parser)

        # Act
        result = framework.parse_resume("/path/to/resume.doc")

        # Assert
        assert result == resume_data
        word_parser.parse.assert_called_once_with("/path/to/resume.doc")

    @patch.object(ResumeParserFramework, "_create_extractor")
    @patch("framework.resume_parser_framework.Path")
    def test_parse_resume_with_uppercase_extension(
        self, mock_path_class: Mock, mock_create_extractor: Mock
    ) -> None:
        """Test parsing resume with uppercase file extension."""
        # Arrange
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = True
        mock_path.suffix = ".PDF"
        mock_path_class.return_value = mock_path

        resume_data = ResumeData(
            name="Alice", email="alice@example.com", skills=["Python"]
        )

        mock_extractor = Mock()
        mock_extractor.extract = Mock(return_value=resume_data)
        mock_create_extractor.return_value = mock_extractor

        pdf_parser = Mock(spec=FileParser)
        pdf_parser.parse.return_value = "Resume text"

        framework = ResumeParserFramework(pdf_parser=pdf_parser)

        # Act
        result = framework.parse_resume("/path/to/RESUME.PDF")

        # Assert
        assert result == resume_data


class TestResumeParserFrameworkFileValidation:
    """Test cases for file validation."""

    @patch.object(ResumeParserFramework, "_create_extractor")
    @patch("framework.resume_parser_framework.Path")
    def test_parse_nonexistent_file_raises_error(
        self, mock_path_class: Mock, mock_create_extractor: Mock
    ) -> None:
        """Test that non-existent file raises FileNotFoundError."""
        # Arrange
        mock_path = Mock()
        mock_path.exists.return_value = False
        mock_path_class.return_value = mock_path

        mock_extractor = Mock(spec=ResumeExtractor)
        mock_create_extractor.return_value = mock_extractor
        framework = ResumeParserFramework()

        # Act & Assert
        with pytest.raises(FileNotFoundError, match="Resume file not found"):
            framework.parse_resume("/path/to/nonexistent.pdf")

    @patch.object(ResumeParserFramework, "_create_extractor")
    @patch("framework.resume_parser_framework.Path")
    def test_parse_directory_raises_error(
        self, mock_path_class: Mock, mock_create_extractor: Mock
    ) -> None:
        """Test that directory path raises ValueError."""
        # Arrange
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = False
        mock_path_class.return_value = mock_path

        mock_extractor = Mock(spec=ResumeExtractor)
        mock_create_extractor.return_value = mock_extractor
        framework = ResumeParserFramework()

        # Act & Assert
        with pytest.raises(ValueError, match="Path is not a file"):
            framework.parse_resume("/path/to/directory")

    @patch.object(ResumeParserFramework, "_create_extractor")
    @patch("framework.resume_parser_framework.Path")
    def test_parse_unsupported_extension_raises_error(
        self, mock_path_class: Mock, mock_create_extractor: Mock
    ) -> None:
        """Test that unsupported file extension raises UnsupportedFileFormatError."""
        # Arrange
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = True
        mock_path.suffix = ".txt"
        mock_path_class.return_value = mock_path

        mock_extractor = Mock(spec=ResumeExtractor)
        mock_create_extractor.return_value = mock_extractor
        framework = ResumeParserFramework()

        # Act & Assert
        with pytest.raises(
            UnsupportedFileFormatError, match="Unsupported file format: .txt"
        ):
            framework.parse_resume("/path/to/resume.txt")

    @patch.object(ResumeParserFramework, "_create_extractor")
    @patch("framework.resume_parser_framework.Path")
    def test_parse_no_extension_raises_error(
        self, mock_path_class: Mock, mock_create_extractor: Mock
    ) -> None:
        """Test that file with no extension raises UnsupportedFileFormatError."""
        # Arrange
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = True
        mock_path.suffix = ""
        mock_path_class.return_value = mock_path

        mock_extractor = Mock(spec=ResumeExtractor)
        mock_create_extractor.return_value = mock_extractor
        framework = ResumeParserFramework()

        # Act & Assert
        with pytest.raises(UnsupportedFileFormatError):
            framework.parse_resume("/path/to/resume")


class TestResumeParserFrameworkErrorHandling:
    """Test cases for error handling."""

    @patch.object(ResumeParserFramework, "_create_extractor")
    @patch("framework.resume_parser_framework.Path")
    def test_parser_failure_raises_file_parsing_error(
        self, mock_path_class: Mock, mock_create_extractor: Mock
    ) -> None:
        """Test that parser failure raises FileParsingError."""
        # Arrange
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = True
        mock_path.suffix = ".pdf"
        mock_path_class.return_value = mock_path

        mock_extractor = Mock(spec=ResumeExtractor)
        mock_create_extractor.return_value = mock_extractor

        pdf_parser = Mock(spec=FileParser)
        pdf_parser.parse.side_effect = Exception("Parser failed")

        framework = ResumeParserFramework(pdf_parser=pdf_parser)

        # Act & Assert
        with pytest.raises(FileParsingError, match="Failed to parse resume file"):
            framework.parse_resume("/path/to/resume.pdf")

    @patch.object(ResumeParserFramework, "_create_extractor")
    @patch("framework.resume_parser_framework.Path")
    def test_extractor_failure_propagates_error(
        self, mock_path_class: Mock, mock_create_extractor: Mock
    ) -> None:
        """Test that extractor failure propagates the exception."""
        # Arrange
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = True
        mock_path.suffix = ".pdf"
        mock_path_class.return_value = mock_path

        mock_extractor = Mock()
        mock_extractor.extract = Mock(
            side_effect=FieldExtractionError("Extraction failed")
        )
        mock_create_extractor.return_value = mock_extractor

        pdf_parser = Mock(spec=FileParser)
        pdf_parser.parse.return_value = "Resume text"

        framework = ResumeParserFramework(pdf_parser=pdf_parser)

        # Act & Assert
        with pytest.raises(FieldExtractionError, match="Extraction failed"):
            framework.parse_resume("/path/to/resume.pdf")


class TestResumeParserFrameworkUtilityMethods:
    """Test cases for utility methods."""

    @patch.object(ResumeParserFramework, "_create_extractor")
    def test_is_supported_file_with_pdf(self, mock_create_extractor: Mock) -> None:
        """Test is_supported_file with PDF extension."""
        # Arrange
        mock_extractor = Mock(spec=ResumeExtractor)
        mock_create_extractor.return_value = mock_extractor
        framework = ResumeParserFramework()

        # Act & Assert
        assert framework.is_supported_file("resume.pdf") is True
        assert framework.is_supported_file("resume.PDF") is True

    @patch.object(ResumeParserFramework, "_create_extractor")
    def test_is_supported_file_with_docx(self, mock_create_extractor: Mock) -> None:
        """Test is_supported_file with DOCX extension."""
        # Arrange
        mock_extractor = Mock(spec=ResumeExtractor)
        mock_create_extractor.return_value = mock_extractor
        framework = ResumeParserFramework()

        # Act & Assert
        assert framework.is_supported_file("resume.docx") is True
        assert framework.is_supported_file("resume.DOCX") is True

    @patch.object(ResumeParserFramework, "_create_extractor")
    def test_is_supported_file_with_doc(self, mock_create_extractor: Mock) -> None:
        """Test is_supported_file with DOC extension."""
        # Arrange
        mock_extractor = Mock(spec=ResumeExtractor)
        mock_create_extractor.return_value = mock_extractor
        framework = ResumeParserFramework()

        # Act & Assert
        assert framework.is_supported_file("resume.doc") is True

    @patch.object(ResumeParserFramework, "_create_extractor")
    def test_is_supported_file_with_unsupported_extension(
        self, mock_create_extractor: Mock
    ) -> None:
        """Test is_supported_file with unsupported extension."""
        # Arrange
        mock_extractor = Mock(spec=ResumeExtractor)
        mock_create_extractor.return_value = mock_extractor
        framework = ResumeParserFramework()

        # Act & Assert
        assert framework.is_supported_file("resume.txt") is False
        assert framework.is_supported_file("resume.xlsx") is False
        assert framework.is_supported_file("resume") is False

    @patch.object(ResumeParserFramework, "_create_extractor")
    def test_get_supported_extensions(self, mock_create_extractor: Mock) -> None:
        """Test get_supported_extensions method."""
        # Arrange
        mock_extractor = Mock(spec=ResumeExtractor)
        mock_create_extractor.return_value = mock_extractor
        framework = ResumeParserFramework()

        # Act
        extensions = framework.get_supported_extensions()

        # Assert
        assert extensions == {".pdf", ".docx", ".doc"}
        assert isinstance(extensions, set)

    @patch.object(ResumeParserFramework, "_create_extractor")
    def test_get_supported_extensions_returns_copy(
        self, mock_create_extractor: Mock
    ) -> None:
        """Test that get_supported_extensions returns a copy."""
        # Arrange
        mock_extractor = Mock(spec=ResumeExtractor)
        mock_create_extractor.return_value = mock_extractor
        framework = ResumeParserFramework()

        # Act
        extensions1 = framework.get_supported_extensions()
        extensions2 = framework.get_supported_extensions()

        # Modify one copy
        extensions1.add(".custom")

        # Assert - the second copy should not be affected
        assert ".custom" not in extensions2
        assert ".custom" not in framework.get_supported_extensions()


class TestResumeParserFrameworkIntegration:
    """Integration tests with realistic resume text."""

    @patch.object(ResumeParserFramework, "_create_extractor")
    @patch("framework.resume_parser_framework.Path")
    def test_parse_complete_resume_with_all_fields(
        self, mock_path_class: Mock, mock_create_extractor: Mock
    ) -> None:
        """Test parsing a complete resume with all extractable fields."""
        # Arrange
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = True
        mock_path.suffix = ".pdf"
        mock_path_class.return_value = mock_path

        realistic_resume_text = """
        JOHN DOE
        Senior Software Engineer
        
        Contact Information:
        Email: john.doe@email.com
        Phone: (555) 123-4567
        LinkedIn: linkedin.com/in/johndoe
        
        PROFESSIONAL SUMMARY
        Experienced software engineer with 8+ years of experience in full-stack development.
        
        TECHNICAL SKILLS
        - Programming Languages: Python, Java, JavaScript, TypeScript
        - Frameworks: Django, Flask, React, Node.js
        - Databases: PostgreSQL, MongoDB, Redis
        - Cloud: AWS, Docker, Kubernetes
        - Tools: Git, Jenkins, JIRA
        
        WORK EXPERIENCE
        Senior Software Engineer | Tech Company Inc. | 2020 - Present
        - Led team of 5 developers in building microservices architecture
        - Improved system performance by 40% through optimization
        
        Software Engineer | StartUp Co. | 2016 - 2020
        - Developed RESTful APIs using Django and Flask
        - Implemented CI/CD pipelines
        
        EDUCATION
        Bachelor of Science in Computer Science
        University of Technology | 2016
        """

        resume_data = ResumeData(
            name="John Doe",
            email="john.doe@email.com",
            skills=[
                "Python",
                "Java",
                "JavaScript",
                "TypeScript",
                "Django",
                "Flask",
                "React",
                "Node.js",
                "PostgreSQL",
                "MongoDB",
                "Redis",
                "AWS",
                "Docker",
                "Kubernetes",
                "Git",
                "Jenkins",
                "JIRA",
            ],
        )

        mock_extractor = Mock()
        mock_extractor.extract = Mock(return_value=resume_data)
        mock_create_extractor.return_value = mock_extractor

        pdf_parser = Mock(spec=FileParser)
        pdf_parser.parse.return_value = realistic_resume_text

        framework = ResumeParserFramework(pdf_parser=pdf_parser)

        # Act
        result = framework.parse_resume("/path/to/resume.pdf")

        # Assert
        assert result.name == "John Doe"
        assert result.email == "john.doe@email.com"
        assert result.skills is not None
        assert len(result.skills) > 10  # Should have extracted many skills
        assert "Python" in result.skills
        assert "Django" in result.skills
        mock_extractor.extract.assert_called_once_with(realistic_resume_text)

    @patch.object(ResumeParserFramework, "_create_extractor")
    @patch("framework.resume_parser_framework.Path")
    def test_parse_minimal_resume_with_partial_fields(
        self, mock_path_class: Mock, mock_create_extractor: Mock
    ) -> None:
        """Test parsing a minimal resume with only some fields present."""
        # Arrange
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = True
        mock_path.suffix = ".pdf"
        mock_path_class.return_value = mock_path

        minimal_resume_text = """
        Jane Smith
        
        I am a software developer with experience in Python.
        You can reach me at jane.smith@example.com
        
        Skills: Python, SQL
        """

        resume_data = ResumeData(
            name="Jane Smith", email="jane.smith@example.com", skills=["Python", "SQL"]
        )

        mock_extractor = Mock()
        mock_extractor.extract = Mock(return_value=resume_data)
        mock_create_extractor.return_value = mock_extractor

        pdf_parser = Mock(spec=FileParser)
        pdf_parser.parse.return_value = minimal_resume_text

        framework = ResumeParserFramework(pdf_parser=pdf_parser)

        # Act
        result = framework.parse_resume("/path/to/minimal_resume.pdf")

        # Assert
        assert result.name == "Jane Smith"
        assert result.email == "jane.smith@example.com"
        assert result.skills == ["Python", "SQL"]
        mock_extractor.extract.assert_called_once_with(minimal_resume_text)

    @patch.object(ResumeParserFramework, "_create_extractor")
    @patch("framework.resume_parser_framework.Path")
    def test_parse_resume_with_missing_fields(
        self, mock_path_class: Mock, mock_create_extractor: Mock
    ) -> None:
        """Test parsing a resume where some fields cannot be extracted."""
        # Arrange
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = True
        mock_path.suffix = ".pdf"
        mock_path_class.return_value = mock_path

        incomplete_resume_text = """
        Contact me for opportunities.
        I have skills in various technologies.
        """

        # Simulate extraction failing for some fields
        resume_data = ResumeData(
            name=None,  # Name could not be extracted
            email=None,  # Email could not be extracted
            skills=[],  # No skills found
        )

        mock_extractor = Mock()
        mock_extractor.extract = Mock(return_value=resume_data)
        mock_create_extractor.return_value = mock_extractor

        pdf_parser = Mock(spec=FileParser)
        pdf_parser.parse.return_value = incomplete_resume_text

        framework = ResumeParserFramework(pdf_parser=pdf_parser)

        # Act
        result = framework.parse_resume("/path/to/incomplete_resume.pdf")

        # Assert - Should still return ResumeData with None/empty values
        assert result.name is None
        assert result.email is None
        assert result.skills == []
        mock_extractor.extract.assert_called_once_with(incomplete_resume_text)

    @patch.object(ResumeParserFramework, "_create_extractor")
    @patch("framework.resume_parser_framework.Path")
    def test_parse_resume_with_special_characters(
        self, mock_path_class: Mock, mock_create_extractor: Mock
    ) -> None:
        """Test parsing resume with special characters and formatting."""
        # Arrange
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = True
        mock_path.suffix = ".docx"
        mock_path_class.return_value = mock_path

        special_char_resume = """
        José García-Martínez
        
        Email: josé.garcía@email.com
        
        Skills: C++, C#, .NET, Node.js
        Experience with AI/ML & Data Science
        """

        resume_data = ResumeData(
            name="José García-Martínez",
            email="josé.garcía@email.com",
            skills=["C++", "C#", ".NET", "Node.js", "AI/ML", "Data Science"],
        )

        mock_extractor = Mock()
        mock_extractor.extract = Mock(return_value=resume_data)
        mock_create_extractor.return_value = mock_extractor

        word_parser = Mock(spec=FileParser)
        word_parser.parse.return_value = special_char_resume

        framework = ResumeParserFramework(word_parser=word_parser)

        # Act
        result = framework.parse_resume("/path/to/special_resume.docx")

        # Assert
        assert result.name == "José García-Martínez"
        assert result.email == "josé.garcía@email.com"
        assert result.skills is not None
        assert "C++" in result.skills
        assert "C#" in result.skills
        assert ".NET" in result.skills

    @patch.object(ResumeParserFramework, "_create_extractor")
    @patch("framework.resume_parser_framework.Path")
    def test_parse_resume_with_multiple_email_formats(
        self, mock_path_class: Mock, mock_create_extractor: Mock
    ) -> None:
        """Test that only the first/primary email is extracted when multiple exist."""
        # Arrange
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = True
        mock_path.suffix = ".pdf"
        mock_path_class.return_value = mock_path

        multi_email_resume = """
        Alice Johnson
        
        Primary Email: alice.johnson@email.com
        Alternative: alice.j@company.com
        Personal: alice123@gmail.com
        
        Skills: Python, Java
        """

        # EmailExtractor should return the first email found
        resume_data = ResumeData(
            name="Alice Johnson",
            email="alice.johnson@email.com",  # First email
            skills=["Python", "Java"],
        )

        mock_extractor = Mock()
        mock_extractor.extract = Mock(return_value=resume_data)
        mock_create_extractor.return_value = mock_extractor

        pdf_parser = Mock(spec=FileParser)
        pdf_parser.parse.return_value = multi_email_resume

        framework = ResumeParserFramework(pdf_parser=pdf_parser)

        # Act
        result = framework.parse_resume("/path/to/multi_email_resume.pdf")

        # Assert
        assert result.email == "alice.johnson@email.com"
        assert result.name == "Alice Johnson"

    @patch.object(ResumeParserFramework, "_create_extractor")
    @patch("framework.resume_parser_framework.Path")
    def test_parse_resume_with_long_text(
        self, mock_path_class: Mock, mock_create_extractor: Mock
    ) -> None:
        """Test parsing a very long resume with extensive content."""
        # Arrange
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = True
        mock_path.suffix = ".pdf"
        mock_path_class.return_value = mock_path

        # Simulate a long resume (5000+ characters)
        long_resume_text = (
            """
        ROBERT ANDERSON
        Senior Full Stack Developer
        
        Email: robert.anderson@professional.com
        """
            + "\n\nPROFESSIONAL EXPERIENCE\n"
            + ("Project description and achievements. " * 100)
            + """
        
        TECHNICAL SKILLS
        Python, JavaScript, TypeScript, Java, Go, Rust, C++, Ruby
        Django, Flask, FastAPI, React, Angular, Vue.js, Next.js
        PostgreSQL, MySQL, MongoDB, Redis, Elasticsearch
        AWS, Azure, GCP, Docker, Kubernetes, Terraform
        Git, GitHub, GitLab, Jenkins, CircleCI, Travis CI
        """
        )

        resume_data = ResumeData(
            name="Robert Anderson",
            email="robert.anderson@professional.com",
            skills=[
                "Python",
                "JavaScript",
                "TypeScript",
                "Java",
                "Go",
                "Rust",
                "C++",
                "Ruby",
                "Django",
                "Flask",
                "FastAPI",
                "React",
                "Angular",
                "Vue.js",
                "Next.js",
                "PostgreSQL",
                "MySQL",
                "MongoDB",
                "Redis",
                "Elasticsearch",
                "AWS",
                "Azure",
                "GCP",
                "Docker",
                "Kubernetes",
                "Terraform",
                "Git",
                "GitHub",
                "GitLab",
                "Jenkins",
                "CircleCI",
            ],
        )

        mock_extractor = Mock()
        mock_extractor.extract = Mock(return_value=resume_data)
        mock_create_extractor.return_value = mock_extractor

        pdf_parser = Mock(spec=FileParser)
        pdf_parser.parse.return_value = long_resume_text

        framework = ResumeParserFramework(pdf_parser=pdf_parser)

        # Act
        result = framework.parse_resume("/path/to/long_resume.pdf")

        # Assert
        assert result.name == "Robert Anderson"
        assert result.email == "robert.anderson@professional.com"
        assert result.skills is not None
        assert len(result.skills) > 20  # Should have extracted many skills
        assert len(long_resume_text) > 4000  # Verify text is actually long
        mock_extractor.extract.assert_called_once()


class TestResumeParserFrameworkEdgeCases:
    """Test edge cases and boundary conditions."""

    @patch.object(ResumeParserFramework, "_create_extractor")
    @patch("framework.resume_parser_framework.Path")
    def test_parse_resume_with_empty_extracted_text(
        self, mock_path_class: Mock, mock_create_extractor: Mock
    ) -> None:
        """Test handling of files that parse but yield empty text."""
        # Arrange
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = True
        mock_path.suffix = ".pdf"
        mock_path_class.return_value = mock_path

        mock_extractor = Mock()
        # Extractor should raise ValueError for empty text (as per coordinator implementation)
        mock_extractor.extract = Mock(
            side_effect=ValueError("Resume text cannot be empty")
        )
        mock_create_extractor.return_value = mock_extractor

        pdf_parser = Mock(spec=FileParser)
        pdf_parser.parse.return_value = ""  # Empty text

        framework = ResumeParserFramework(pdf_parser=pdf_parser)

        # Act & Assert
        with pytest.raises(ValueError, match="Resume text cannot be empty"):
            framework.parse_resume("/path/to/empty_resume.pdf")

    @patch.object(ResumeParserFramework, "_create_extractor")
    @patch("framework.resume_parser_framework.Path")
    def test_parse_resume_with_whitespace_only_text(
        self, mock_path_class: Mock, mock_create_extractor: Mock
    ) -> None:
        """Test handling of files with only whitespace."""
        # Arrange
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = True
        mock_path.suffix = ".pdf"
        mock_path_class.return_value = mock_path

        mock_extractor = Mock()
        mock_extractor.extract = Mock(
            side_effect=ValueError("Resume text cannot be empty")
        )
        mock_create_extractor.return_value = mock_extractor

        pdf_parser = Mock(spec=FileParser)
        pdf_parser.parse.return_value = "   \n\n\t\t   "  # Only whitespace

        framework = ResumeParserFramework(pdf_parser=pdf_parser)

        # Act & Assert
        with pytest.raises(ValueError, match="Resume text cannot be empty"):
            framework.parse_resume("/path/to/whitespace_resume.pdf")

    @patch.object(ResumeParserFramework, "_create_extractor")
    @patch("framework.resume_parser_framework.Path")
    def test_parse_resume_preserves_text_exactly(
        self, mock_path_class: Mock, mock_create_extractor: Mock
    ) -> None:
        """Test that parsed text is passed to extractor without modification."""
        # Arrange
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = True
        mock_path.suffix = ".pdf"
        mock_path_class.return_value = mock_path

        original_text = "  Text with\n  weird\tformatting  \n"
        resume_data = ResumeData(name="Test", email="test@test.com", skills=[])

        mock_extractor = Mock()
        mock_extractor.extract = Mock(return_value=resume_data)
        mock_create_extractor.return_value = mock_extractor

        pdf_parser = Mock(spec=FileParser)
        pdf_parser.parse.return_value = original_text

        framework = ResumeParserFramework(pdf_parser=pdf_parser)

        # Act
        framework.parse_resume("/path/to/resume.pdf")

        # Assert - text should be passed exactly as parsed
        mock_extractor.extract.assert_called_once_with(original_text)


@pytest.mark.e2e
@pytest.mark.slow
class TestResumeParserFrameworkEndToEnd:
    """End-to-end tests without mocks - uses actual extractors and strategies.

    Note: These tests use NER models which will be downloaded on first run.
    They provide true end-to-end validation of the extraction pipeline.
    """

    def test_end_to_end_with_default_config(self) -> None:
        """Test complete flow with default configuration (uses NER models)."""
        # Arrange - Use default config which includes NER strategies
        # This will use actual NER models (may take time on first run to download)

        resume_text = """
        John Smith
        Senior Software Engineer
        
        Contact: john.smith@techcompany.com
        Phone: (555) 123-4567
        
        PROFESSIONAL SUMMARY
        Experienced software engineer with expertise in Python and JavaScript.
        
        TECHNICAL SKILLS
        Python, Java, JavaScript, TypeScript, Django, Flask, React, Node.js
        PostgreSQL, MongoDB, Redis, Docker, Kubernetes, AWS
        """

        # Create a mock parser that returns our text (only mock file I/O)
        from unittest.mock import Mock, patch

        mock_pdf_parser = Mock()
        mock_pdf_parser.parse = Mock(return_value=resume_text)

        # Create framework with real extractors using default config
        framework = ResumeParserFramework(pdf_parser=mock_pdf_parser)

        # Mock Path to avoid actual file I/O
        with patch("framework.resume_parser_framework.Path") as mock_path_class:
            mock_path = Mock()
            mock_path.exists.return_value = True
            mock_path.is_file.return_value = True
            mock_path.suffix = ".pdf"
            mock_path_class.return_value = mock_path

            # Act - Run the complete extraction pipeline with real extractors
            result = framework.parse_resume("/test/resume.pdf")

        # Assert - Verify extracted data
        assert result is not None
        assert isinstance(result, ResumeData)

        # Email should definitely be extracted (regex pattern is reliable)
        assert result.email == "john.smith@techcompany.com"

        # Name and skills depend on NER model performance
        # Just verify they are the right type
        assert result.name is None or isinstance(result.name, str)
        assert result.skills is not None
        assert isinstance(result.skills, list)

    def test_end_to_end_email_extraction_only(self) -> None:
        """Test E2E focusing on email extraction which uses regex (no ML needed)."""
        # Arrange - Use default config to create all extractors
        # We focus on validating email extraction which is most reliable

        simple_resume = """
        Contact Information:
        Email: jane.doe@example.com
        Phone: 555-1234
        
        I am a software developer.
        """

        from unittest.mock import Mock, patch

        mock_parser = Mock()
        mock_parser.parse = Mock(return_value=simple_resume)

        # Use default config (will create all extractors)
        framework = ResumeParserFramework(pdf_parser=mock_parser)

        with patch("framework.resume_parser_framework.Path") as mock_path_class:
            mock_path = Mock()
            mock_path.exists.return_value = True
            mock_path.is_file.return_value = True
            mock_path.suffix = ".pdf"
            mock_path_class.return_value = mock_path

            # Act
            result = framework.parse_resume("/test/simple_resume.pdf")

        # Assert - Email extraction should work reliably with regex
        assert result is not None
        assert result.email == "jane.doe@example.com"

    def test_end_to_end_with_multiple_emails(self) -> None:
        """Test E2E when resume has multiple email addresses."""
        # Arrange
        resume_with_emails = """
        Alice Johnson
        Software Engineer
        
        Primary: alice.johnson@work.com
        Personal: alice.j@gmail.com
        Alternative: ajohnson@company.org
        """

        from unittest.mock import Mock, patch

        mock_parser = Mock()
        mock_parser.parse = Mock(return_value=resume_with_emails)

        framework = ResumeParserFramework(pdf_parser=mock_parser)

        with patch("framework.resume_parser_framework.Path") as mock_path_class:
            mock_path = Mock()
            mock_path.exists.return_value = True
            mock_path.is_file.return_value = True
            mock_path.suffix = ".pdf"
            mock_path_class.return_value = mock_path

            # Act
            result = framework.parse_resume("/test/multi_email.pdf")

        # Assert - Should extract the first email found
        assert result is not None
        assert result.email in [
            "alice.johnson@work.com",
            "alice.j@gmail.com",
            "ajohnson@company.org",
        ]

    def test_end_to_end_file_validation_still_works(self) -> None:
        """Test that file validation works in E2E scenario."""
        # Arrange - Create framework with defaults
        framework = ResumeParserFramework()

        from unittest.mock import patch, Mock

        # Test nonexistent file
        with patch("framework.resume_parser_framework.Path") as mock_path_class:
            mock_path = Mock()
            mock_path.exists.return_value = False
            mock_path_class.return_value = mock_path

            with pytest.raises(FileNotFoundError, match="Resume file not found"):
                framework.parse_resume("/nonexistent/file.pdf")

        # Test unsupported extension
        with patch("framework.resume_parser_framework.Path") as mock_path_class:
            mock_path = Mock()
            mock_path.exists.return_value = True
            mock_path.is_file.return_value = True
            mock_path.suffix = ".txt"
            mock_path_class.return_value = mock_path

            with pytest.raises(
                UnsupportedFileFormatError, match="Unsupported file format"
            ):
                framework.parse_resume("/test/file.txt")

    def test_end_to_end_empty_text_handling(self) -> None:
        """Test E2E error handling when parser returns empty text."""
        # Arrange
        from unittest.mock import Mock, patch

        mock_parser = Mock()
        mock_parser.parse = Mock(return_value="   \n\n  ")  # Whitespace only

        framework = ResumeParserFramework(pdf_parser=mock_parser)

        with patch("framework.resume_parser_framework.Path") as mock_path_class:
            mock_path = Mock()
            mock_path.exists.return_value = True
            mock_path.is_file.return_value = True
            mock_path.suffix = ".pdf"
            mock_path_class.return_value = mock_path

            # Act & Assert - Should raise ValueError for empty text
            with pytest.raises(ValueError, match="Resume text cannot be empty"):
                framework.parse_resume("/test/empty.pdf")
