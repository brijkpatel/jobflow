"""Main entry point for parsing resumes.

Handles PDF/DOCX files and extracts all structured resume fields.
"""

from pathlib import Path
from typing import Dict, Optional, List, Any

from interfaces import FileParser, FieldType, FieldExtractor
from coordinators import ResumeExtractor
from extractors import ExperienceAnalyticsExtractor
from models import ResumeData
from parsers import PDFParser, WordParser
from extractors import create_extractor
from config import ExtractionConfig, DEFAULT_EXTRACTION_CONFIG
from exceptions import UnsupportedFileFormatError, FileParsingError
from utils import logger


class ResumeParserFramework:
    """Parse resumes from PDF/DOCX files and extract all structured data.

    Usage:
        framework = ResumeParserFramework()
        data = framework.parse_resume("resume.pdf")
        print(data.to_json())

    How it works:
        1. Validates file exists and format is supported
        2. Parses file to extract raw text (PDF or Word)
        3. Runs field extractors (Regex / NER / LLM) for every configured field
        4. Computes experience analytics from work history
        5. Returns fully populated ResumeData

    Supports: .pdf, .docx, .doc files
    """

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc"}

    def __init__(
        self,
        config: Optional[ExtractionConfig] = None,
        pdf_parser: Optional[FileParser] = None,
        word_parser: Optional[FileParser] = None,
    ):
        """Initialize the framework.

        Args:
            config: Extraction config (uses DEFAULT_EXTRACTION_CONFIG if not provided)
            pdf_parser: Custom PDF parser (optional)
            word_parser: Custom Word parser (optional)
        """
        self.config = config or DEFAULT_EXTRACTION_CONFIG

        self.parsers: Dict[str, FileParser] = {
            ".pdf": pdf_parser or PDFParser(),
            ".docx": word_parser or WordParser(),
            ".doc": word_parser or WordParser(),
        }

        self.extractor = self._create_extractor()

        logger.info(
            f"ResumeParserFramework initialized with {len(self.parsers)} parsers "
            f"and config-driven extractors"
        )

    def _create_extractor(self) -> ResumeExtractor:
        """Build extractors for every configured field type.

        Returns:
            ResumeExtractor ready to extract all fields
        """
        logger.debug("Creating field extractors from configuration")

        extractors_dict: Dict[FieldType, List[FieldExtractor[Any]]] = {}

        for field_type, strategies in self.config.strategy_preferences.items():
            field_extractors: List[FieldExtractor[Any]] = []

            for strategy_type in strategies:
                try:
                    extractor = create_extractor(field_type, strategy_type)
                    field_extractors.append(extractor)
                    logger.debug(
                        f"Created {strategy_type.value} extractor for {field_type.value}"
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to create {strategy_type.value} extractor for "
                        f"{field_type.value}: {e}. Skipping."
                    )

            if field_extractors:
                extractors_dict[field_type] = field_extractors
            else:
                logger.warning(
                    f"No working extractors for '{field_type.value}' — field will be skipped."
                )

        return ResumeExtractor(
            extractors_dict,
            analytics_extractor=ExperienceAnalyticsExtractor(),
        )

    def parse_resume(self, file_path: str) -> ResumeData:
        """Parse a resume file and extract all structured data.

        Args:
            file_path: Path to resume file (.pdf, .docx, or .doc)

        Returns:
            Fully populated ResumeData

        Raises:
            FileNotFoundError: File doesn't exist
            UnsupportedFileFormatError: File type not supported
            FileParsingError: Can't extract text from file
        """
        logger.info(f"Starting resume parsing: {file_path}")

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Resume file not found: {file_path}")
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        extension = path.suffix.lower()
        if extension not in self.SUPPORTED_EXTENSIONS:
            raise UnsupportedFileFormatError(
                f"Unsupported file format: {extension}. "
                f"Supported: {', '.join(sorted(self.SUPPORTED_EXTENSIONS))}"
            )

        parser = self.parsers.get(extension)
        if not parser:
            raise UnsupportedFileFormatError(
                f"No parser configured for {extension} files"
            )

        logger.info(f"Using parser: {parser.__class__.__name__}")

        try:
            text = parser.parse(file_path)
            logger.info(f"Extracted {len(text)} characters from file")
        except Exception as e:
            raise FileParsingError(
                f"Failed to parse resume file: {file_path}", original_exception=e
            ) from e

        try:
            resume_data = self.extractor.extract(text)
            logger.info(f"Parsing complete: {resume_data}")
            return resume_data
        except Exception as e:
            logger.error(f"Field extraction failed: {e}")
            raise

    def is_supported_file(self, file_path: str) -> bool:
        """Check if file format is supported."""
        return Path(file_path).suffix.lower() in self.SUPPORTED_EXTENSIONS

    def get_supported_extensions(self) -> set[str]:
        """Get set of supported file extensions."""
        return self.SUPPORTED_EXTENSIONS.copy()
