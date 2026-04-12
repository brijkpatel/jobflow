"""Comprehensive tests for PDF parser."""

import pytest
from pathlib import Path
from parsers.pdf_parser import PDFParser
from exceptions import FileParsingError


# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "data"


class TestPDFParserInitialization:
    """Test PDF parser initialization."""

    def test_initialization(self):
        """Test that PDFParser initializes correctly."""
        parser = PDFParser()
        assert parser is not None
        assert parser.supported_extensions == [".pdf"]


class TestPDFParserValidFiles:
    """Test PDF parser with valid files."""

    @pytest.fixture
    def parser(self):
        """Create a PDFParser instance."""
        return PDFParser()

    def test_parse_valid_pdf(self, parser: PDFParser):
        """Test parsing a valid PDF file."""
        pdf_file = TEST_DATA_DIR / "valid_resume.pdf"
        if not pdf_file.exists():
            pytest.skip(f"Test file {pdf_file} does not exist")

        text = parser.parse(str(pdf_file))
        assert isinstance(text, str)
        assert len(text) > 0
        assert text.strip() != ""
        assert "John Doe" in text or "Test Resume" in text

    def test_parse_multipage_pdf(self, parser: PDFParser):
        """Test parsing a multi-page PDF."""
        pdf_file = TEST_DATA_DIR / "multipage.pdf"
        if not pdf_file.exists():
            pytest.skip(f"Test file {pdf_file} does not exist")

        text = parser.parse(str(pdf_file))
        assert isinstance(text, str)
        assert len(text) > 0

    def test_parsed_text_cleanup(self, parser: PDFParser):
        """Test that parsed text is properly cleaned."""
        pdf_file = TEST_DATA_DIR / "valid_resume.pdf"
        if not pdf_file.exists():
            pytest.skip(f"Test file {pdf_file} does not exist")

        text = parser.parse(str(pdf_file))
        # Check that excessive whitespace is removed
        assert "  " not in text or text.count("  ") < len(text) // 10
        # Check that text has line breaks (structure preserved)
        assert "\n" in text


class TestPDFParserInvalidFiles:
    """Test PDF parser with invalid files."""

    @pytest.fixture
    def parser(self):
        """Create a PDFParser instance."""
        return PDFParser()

    def test_parse_nonexistent_file(self, parser: PDFParser):
        """Test parsing a file that doesn't exist."""
        with pytest.raises(FileNotFoundError):
            parser.parse(str(TEST_DATA_DIR / "nonexistent.pdf"))

    def test_parse_empty_pdf(self, parser: PDFParser):
        """Test parsing an empty PDF file."""
        empty_pdf = TEST_DATA_DIR / "empty.pdf"
        if not empty_pdf.exists():
            pytest.skip(f"Test file {empty_pdf} does not exist")

        with pytest.raises(FileParsingError):
            parser.parse(str(empty_pdf))

    def test_parse_corrupted_pdf(self, parser: PDFParser):
        """Test parsing a corrupted PDF file."""
        corrupted_pdf = TEST_DATA_DIR / "corrupted.pdf"
        if not corrupted_pdf.exists():
            pytest.skip(f"Test file {corrupted_pdf} does not exist")

        with pytest.raises(FileParsingError) as exc_info:
            parser.parse(str(corrupted_pdf))
        assert exc_info.value.original_exception is not None

    def test_parse_text_file_as_pdf(self, parser: PDFParser):
        """Test parsing a text file with .pdf extension."""
        fake_pdf = TEST_DATA_DIR / "fake.pdf"
        if not fake_pdf.exists():
            pytest.skip(f"Test file {fake_pdf} does not exist")

        with pytest.raises(FileParsingError):
            parser.parse(str(fake_pdf))

    def test_parse_non_pdf_file(self, parser: PDFParser):
        """Test parsing a non-PDF file."""
        non_pdf = TEST_DATA_DIR / "sample.txt"
        if not non_pdf.exists():
            pytest.skip(f"Test file {non_pdf} does not exist")

        with pytest.raises(FileParsingError):
            parser.parse(str(non_pdf))

    def test_parse_directory(self, parser: PDFParser):
        """Test parsing a directory path."""
        with pytest.raises(FileParsingError):
            parser.parse(str(TEST_DATA_DIR))


class TestPDFParserSupportsFormat:
    """Test PDF parser format support checking."""

    @pytest.fixture
    def parser(self):
        """Create a PDFParser instance."""
        return PDFParser()

    def test_supports_pdf_extension(self, parser: PDFParser):
        """Test that .pdf extension is supported."""
        assert parser.supports_format("test.pdf")
        assert parser.supports_format("TEST.PDF")
        assert parser.supports_format("/path/to/file.pdf")

    def test_does_not_support_other_extensions(self, parser: PDFParser):
        """Test that non-PDF extensions are not supported."""
        assert not parser.supports_format("test.docx")
        assert not parser.supports_format("test.txt")
        assert not parser.supports_format("test.doc")
        assert not parser.supports_format("test.xlsx")
        assert not parser.supports_format("test")

    def test_supports_format_with_path_object(self, parser: PDFParser):
        """Test supports_format with Path object."""
        assert parser.supports_format(Path("test.pdf"))
        assert not parser.supports_format(Path("test.docx"))


class TestPDFParserEdgeCases:
    """Test PDF parser edge cases."""

    @pytest.fixture
    def parser(self):
        """Create a PDFParser instance."""
        return PDFParser()

    def test_parse_pdf_with_images_only(self, parser: PDFParser):
        """Test parsing a PDF with only images (no text)."""
        image_pdf = TEST_DATA_DIR / "images_only.pdf"
        if not image_pdf.exists():
            pytest.skip(f"Test file {image_pdf} does not exist")

        with pytest.raises(FileParsingError) as exc_info:
            parser.parse(str(image_pdf))
        assert "No text content found in PDF" in str(exc_info.value)

    def test_parse_password_protected_pdf(self, parser: PDFParser):
        """Test parsing a password-protected PDF."""
        protected_pdf = TEST_DATA_DIR / "password_protected.pdf"
        if not protected_pdf.exists():
            pytest.skip(f"Test file {protected_pdf} does not exist")

        with pytest.raises(FileParsingError):
            parser.parse(str(protected_pdf))

    def test_parse_pdf_with_special_characters(self, parser: PDFParser):
        """Test parsing a PDF with special characters."""
        special_pdf = TEST_DATA_DIR / "special_chars.pdf"
        if not special_pdf.exists():
            pytest.skip(f"Test file {special_pdf} does not exist")

        text = parser.parse(str(special_pdf))
        assert isinstance(text, str)
        assert len(text) > 0

    def test_parse_pdf_with_tables(self, parser: PDFParser):
        """Test parsing a PDF with tables."""
        table_pdf = TEST_DATA_DIR / "with_tables.pdf"
        if not table_pdf.exists():
            pytest.skip(f"Test file {table_pdf} does not exist")

        text = parser.parse(str(table_pdf))
        assert isinstance(text, str)
        assert len(text) > 0

    def test_parse_very_large_pdf(self, parser: PDFParser):
        """Test parsing a very large PDF file."""
        large_pdf = TEST_DATA_DIR / "large.pdf"
        if not large_pdf.exists():
            pytest.skip(f"Test file {large_pdf} does not exist")

        text = parser.parse(str(large_pdf))
        assert isinstance(text, str)
        assert len(text) > 1000  # Should have substantial content

    def test_clean_extracted_text_empty_string(self, parser: PDFParser):
        """Test _clean_extracted_text with empty string."""
        result = parser._clean_extracted_text("")
        assert result == ""

    def test_clean_extracted_text_whitespace_only(self, parser: PDFParser):
        """Test _clean_extracted_text with whitespace only."""
        result = parser._clean_extracted_text("   \n   \n   ")
        assert result == ""

    def test_clean_extracted_text_with_excessive_spaces(self, parser: PDFParser):
        """Test _clean_extracted_text with excessive spaces."""
        text = "Hello    world\nThis   is    a   test"
        result = parser._clean_extracted_text(text)
        assert "Hello world" in result
        assert "This is a test" in result
        assert "    " not in result

    def test_clean_extracted_text_preserves_line_breaks(self, parser: PDFParser):
        """Test that _clean_extracted_text preserves line breaks."""
        text = "Line 1\nLine 2\nLine 3"
        result = parser._clean_extracted_text(text)
        assert result.count("\n") == 2
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result
