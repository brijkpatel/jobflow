"""Extract text from PDF files using PDFMiner."""

from pathlib import Path
from typing import Union, List

from pdfminer.high_level import extract_text

from interfaces.file_parser import FileParser
from exceptions import FileParsingError
from utils import logger


class PDFParser(FileParser):
    """Parse PDF files and extract text content."""

    def __init__(self):
        """Initialize the PDF parser."""
        self.supported_extensions = [".pdf"]
        logger.debug("PDFParser initialized")

    def parse(self, file_path: str) -> str:
        """Extract text from PDF file.

        Steps:
            1. Validate file path
            2. Use PDFMiner to extract text
            3. Clean up extracted text
            4. Return cleaned text

        Args:
            file_path: Path to PDF file

        Returns:
            Cleaned text content

        Raises:
            FileParsingError: If parsing fails
        """
        self._validate_file_path(file_path)

        try:
            logger.info("Starting PDF parsing: %s", file_path)

            # Extract text using PDFMiner
            text = extract_text(file_path)

            if not text or not text.strip():
                raise FileParsingError("No text content found in PDF.")

            # Clean up text
            cleaned_text = self._clean_extracted_text(text)

            logger.info(
                "Successfully parsed PDF: %s (%d characters)",
                file_path,
                len(cleaned_text),
            )
            return cleaned_text

        except FileParsingError:
            raise
        except Exception as e:
            raise FileParsingError("PDF parsing failed.", original_exception=e) from e

    def _clean_extracted_text(self, text: str) -> str:
        """Remove excess whitespace while keeping line breaks."""
        if not text:
            return ""

        lines: List[str] = []
        for line in text.split("\n"):
            cleaned_line = " ".join(line.split())
            if cleaned_line:
                lines.append(cleaned_line)

        return "\n".join(lines)

    def supports_format(self, file_path: Union[str, Path]) -> bool:
        """Check if file is a PDF."""
        extension = self._get_file_extension(file_path)
        return extension in self.supported_extensions
