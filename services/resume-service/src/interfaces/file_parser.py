"""Base class for file parsers."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union

from exceptions import FileParsingError
from utils import logger


class FileParser(ABC):
    """Base class for parsing files to extract text.

    Implemented by: PDFParser, WordParser
    """

    @abstractmethod
    def parse(self, file_path: str) -> str:
        """Parse file and extract text.

        Args:
            file_path: Path to file

        Returns:
            Extracted text content

        Raises:
            FileParsingError: If parsing fails
            FileNotFoundError: If file doesn't exist
        """

    @abstractmethod
    def supports_format(self, file_path: Union[str, Path]) -> bool:
        """Check if this parser supports the file format."""

    def _validate_file_path(self, file_path: Union[str, Path]) -> None:
        """Check file exists and is readable."""
        path_obj = Path(file_path)

        if not path_obj.exists():
            raise FileNotFoundError(f"File not found: {path_obj}")

        if not path_obj.is_file():
            raise FileParsingError("Path is not a file.")

        if not path_obj.stat().st_size > 0:
            logger.warning("File appears to be empty: %s", path_obj)

        # Check readability
        try:
            with open(path_obj, "rb") as f:
                f.read(1)
        except PermissionError as exc:
            raise FileParsingError(
                "File is not readable.", original_exception=exc
            ) from exc
        except Exception as exc:
            raise FileParsingError(
                "Error reading file.", original_exception=exc
            ) from exc

    def _get_file_extension(self, file_path: Union[str, Path]) -> str:
        """Get file extension in lowercase (includes dot)."""
        return Path(file_path).suffix.lower()
