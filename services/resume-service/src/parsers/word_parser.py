"""Extract text from Word documents (.docx and .doc files)."""

from pathlib import Path
from typing import Union, List

from docx import Document

from interfaces import FileParser
from exceptions import FileParsingError
from utils import logger


class WordParser(FileParser):
    """Parse Word documents and extract text content."""

    def __init__(self):
        """Initialize the Word parser."""
        self.supported_extensions = [".docx", ".doc"]
        logger.debug("WordParser initialized")

    def parse(self, file_path: str) -> str:
        """Extract text from Word document.

        Steps:
            1. Validate file path
            2. Check if legacy .doc or modern .docx
            3. Extract text from paragraphs and tables
            4. Return combined text

        Args:
            file_path: Path to Word document

        Returns:
            Extracted text content

        Raises:
            FileParsingError: If parsing fails
        """
        self._validate_file_path(file_path)

        if not self.supports_format(file_path):
            raise FileParsingError("Unsupported file format.")

        logger.info("Parsing Word document: %s", file_path)

        # Handle legacy .doc files
        if self._get_file_extension(file_path) == ".doc":
            return self._parse_doc_file(file_path)

        # Parse .docx files
        try:
            document = Document(file_path)
            text_content: List[str] = []

            # Extract from paragraphs
            for paragraph in document.paragraphs:
                text = paragraph.text.strip()
                if text:
                    text_content.append(text)

            # Extract from tables
            for table in document.tables:
                for row in table.rows:
                    row_text: List[str] = []
                    for cell in row.cells:
                        cell_text = cell.text.strip()
                        if cell_text:
                            row_text.append(cell_text)
                    if row_text:
                        text_content.append(" | ".join(row_text))

            if not text_content:
                raise FileParsingError("No text content found in document.")

            full_text = "\n".join(text_content)

            logger.info(
                "Successfully parsed Word document: %s (%d characters)",
                file_path,
                len(full_text),
            )

            return full_text

        except Exception as e:
            raise FileParsingError(
                "Error parsing Word document.", original_exception=e
            ) from e

    def _parse_doc_file(self, file_path: str) -> str:
        """Try to parse legacy .doc files.

        Note: python-docx doesn't fully support .doc format.
        Works with some files, fails with others.

        Args:
            file_path: Path to .doc file

        Returns:
            Extracted text

        Raises:
            FileParsingError: If parsing fails
        """
        logger.warning("Legacy .doc format detected: %s", file_path)

        try:
            # Try python-docx (sometimes works with newer .doc files)
            document = Document(file_path)
            text_content: List[str] = []

            for paragraph in document.paragraphs:
                text = paragraph.text.strip()
                if text:
                    text_content.append(text)

            if text_content:
                full_text = "\n".join(text_content)
                logger.info("Successfully parsed .doc file using docx: %s", file_path)
                return full_text

        except Exception as e:
            raise FileParsingError(
                "Error parsing Word document.", original_exception=e
            ) from e

        raise FileParsingError(
            "Cannot parse legacy .doc file. Please convert to .docx format or use a tool like LibreOffice to convert the file."
        )

    def supports_format(self, file_path: Union[str, Path]) -> bool:
        """Check if file is a Word document."""
        extension = self._get_file_extension(file_path)
        return extension in self.supported_extensions
