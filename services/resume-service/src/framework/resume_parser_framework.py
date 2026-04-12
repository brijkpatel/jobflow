"""Main entry point for parsing resumes.

Simple interface that handles PDF/DOCX files and extracts name, email, and skills.
"""

from pathlib import Path
from typing import Dict, Optional, List, Any

from interfaces import FileParser, FieldType, FieldExtractor
from coordinators import ResumeExtractor
from models import ResumeData
from parsers import PDFParser, WordParser
from extractors import create_extractor
from config import ExtractionConfig, DEFAULT_EXTRACTION_CONFIG
from exceptions import UnsupportedFileFormatError, FileParsingError
from utils import logger


class ResumeParserFramework:
    """Parse resumes from PDF/DOCX files and extract structured data.

    Usage:
        framework = ResumeParserFramework()
        data = framework.parse_resume("resume.pdf")
        print(data.name, data.email, data.skills)

    How it works:
        1. Validates file exists and format is supported
        2. Parses file to extract text (PDF or Word)
        3. Runs extractors to find name, email, skills
        4. Returns ResumeData with extracted fields

    Supports: .pdf, .docx, .doc files
    """

    # Supported file extensions
    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc"}

    def __init__(
        self,
        config: Optional[ExtractionConfig] = None,
        pdf_parser: Optional[FileParser] = None,
        word_parser: Optional[FileParser] = None,
    ):
        """Initialize the framework.

        Args:
            config: Extraction config (uses default if not provided)
            pdf_parser: Custom PDF parser (optional)
            word_parser: Custom Word parser (optional)
        """
        self.config = config or DEFAULT_EXTRACTION_CONFIG

        # Set up file parsers
        self.parsers: Dict[str, FileParser] = {
            ".pdf": pdf_parser or PDFParser(),
            ".docx": word_parser or WordParser(),
            ".doc": word_parser or WordParser(),
        }

        # Create field extractors based on configuration
        self.extractor = self._create_extractor()

        logger.info(
            f"ResumeParserFramework initialized with {len(self.parsers)} parsers "
            f"and config-driven extractors"
        )

    def _create_extractor(self) -> ResumeExtractor:
        """Create extractors for each field based on configuration.

        Steps:
            1. Get strategy list for each field from config
            2. Create extractor for each strategy
            3. Build extractor chain with fallback
            4. Return ResumeExtractor with all extractors

        Returns:
            ResumeExtractor ready to extract all fields
        """
        logger.debug("Creating field extractors from configuration")

        extractors_dict: Dict[FieldType, List[FieldExtractor[Any]]] = {}

        # Create extractors for name, email, skills
        for field_type in [FieldType.NAME, FieldType.EMAIL, FieldType.SKILLS]:
            strategies = self.config.get_strategies_for_field(field_type)
            field_extractors: List[FieldExtractor[Any]] = []

            logger.debug(
                f"Creating {len(strategies)} extractor(s) for {field_type.value}"
            )

            # Try to create each strategy's extractor
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
                        f"{field_type.value}: {e}. Skipping this strategy."
                    )
                    continue

            # Must have at least one working extractor
            if not field_extractors:
                logger.error(f"No extractors could be created for {field_type.value}")
                raise RuntimeError(
                    f"Failed to create any extractors for {field_type.value}"
                )

            extractors_dict[field_type] = field_extractors

        return ResumeExtractor(extractors_dict)

    def parse_resume(self, file_path: str) -> ResumeData:
        """Parse a resume file and extract name, email, and skills.

        Steps:
            1. Check file exists and is supported format
            2. Select appropriate parser (PDF or Word)
            3. Extract text from file
            4. Run extractors to find fields
            5. Return structured data

        Args:
            file_path: Path to resume file (.pdf, .docx, or .doc)

        Returns:
            ResumeData with extracted name, email, and skills

        Raises:
            FileNotFoundError: File doesn't exist
            UnsupportedFileFormatError: File type not supported
            FileParsingError: Can't parse file
            FieldExtractionError: Can't extract fields
        """
        logger.info(f"Starting resume parsing for file: {file_path}")

        # Step 1: Validate file
        path = Path(file_path)
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"Resume file not found: {file_path}")

        if not path.is_file():
            logger.error(f"Path is not a file: {file_path}")
            raise ValueError(f"Path is not a file: {file_path}")

        # Step 2: Check file extension
        extension = path.suffix.lower()
        logger.debug(f"Detected file extension: {extension}")

        if extension not in self.SUPPORTED_EXTENSIONS:
            logger.error(f"Unsupported file format: {extension}")
            raise UnsupportedFileFormatError(
                f"Unsupported file format: {extension}. "
                f"Supported formats: {', '.join(sorted(self.SUPPORTED_EXTENSIONS))}"
            )

        # Step 3: Get parser for this file type
        parser = self.parsers.get(extension)
        if not parser:
            logger.error(f"No parser found for extension: {extension}")
            raise UnsupportedFileFormatError(
                f"No parser configured for {extension} files"
            )

        logger.info(f"Using parser: {parser.__class__.__name__}")

        # Step 4: Parse file to get text
        try:
            text = parser.parse(file_path)
            logger.info(f"Successfully parsed file, extracted {len(text)} characters")
        except Exception as e:
            logger.error(f"File parsing failed: {e}")
            raise FileParsingError(
                f"Failed to parse resume file: {file_path}", original_exception=e
            ) from e

        # Step 5: Extract fields from text
        try:
            resume_data = self.extractor.extract(text)
            skills_count = len(resume_data.skills) if resume_data.skills else 0
            logger.info(
                f"Successfully extracted resume data: {resume_data.name}, "
                f"{resume_data.email}, {skills_count} skills"
            )
            return resume_data
        except Exception as e:
            logger.error(f"Field extraction failed: {e}")
            raise

    def is_supported_file(self, file_path: str) -> bool:
        """Check if file format is supported."""
        extension = Path(file_path).suffix.lower()
        return extension in self.SUPPORTED_EXTENSIONS

    def get_supported_extensions(self) -> set[str]:
        """Get set of supported file extensions."""
        return self.SUPPORTED_EXTENSIONS.copy()
