"""Init file for exceptions package."""

from .base_exception import ResumeParserException
from .api_exceptions import ExternalServiceError
from .parsing_exceptions import (
    FileParsingError,
    FieldExtractionError,
    UnsupportedFileFormatError,
    InvalidConfigurationError,
    StrategyExtractionError,
    InvalidStrategyConfigError,
    NoMatchFoundError,
)

__all__ = [
    "ResumeParserException",
    "ExternalServiceError",
    "FileParsingError",
    "FieldExtractionError",
    "UnsupportedFileFormatError",
    "InvalidConfigurationError",
    "StrategyExtractionError",
    "InvalidStrategyConfigError",
    "NoMatchFoundError",
]
