"""Pytest configuration and fixtures for the entire project."""

from pathlib import Path
import pytest
from dotenv import load_dotenv

# Load environment variables from .env file
# This ensures tests have access to API keys and other config
load_dotenv()

# Get src directory path
src_path = Path(__file__).parent


@pytest.fixture(scope="session", autouse=True)
def setup_parser_test_data():
    """Generate test data files for parser tests before running tests."""
    data_dir = src_path / "parsers" / "tests" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    try:
        from parsers.tests.generate_test_pdfs import (
            create_simple_pdf,
            create_pdf_with_tables,
            create_multipage_pdf,
            create_pdf_with_special_chars,
        )
        from parsers.tests.generate_test_data import (
            create_simple_docx,
            create_docx_with_tables,
            create_empty_content_docx,
        )

        # Generate test files
        # PDF files
        create_simple_pdf()
        create_pdf_with_tables()
        create_multipage_pdf()
        create_pdf_with_special_chars()

        # DOCX files
        create_simple_docx()
        create_docx_with_tables()
        create_empty_content_docx()

        # Create invalid/edge case files
        # Empty files
        (data_dir / "empty.pdf").write_bytes(b"")
        (data_dir / "empty.docx").write_bytes(b"")

        # Corrupted files (text content with wrong extension)
        (data_dir / "corrupted.pdf").write_text("corrupted content")
        (data_dir / "corrupted.docx").write_text("corrupted content")

        # Fake files
        (data_dir / "fake.pdf").write_text("This is not a PDF file")
        (data_dir / "fake.docx").write_text("This is not a DOCX file")

        # Text file
        (data_dir / "sample.txt").write_text(
            "This is a plain text file.\nIt should not be parsed as a PDF or DOCX."
        )

    except Exception as e:
        # Don't fail if test data generation fails - tests will skip as needed
        print(f"Warning: Failed to generate test data: {e}")

    yield
