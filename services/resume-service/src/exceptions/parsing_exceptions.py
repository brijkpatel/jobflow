"""Custom exceptions while parsing Resume."""

from exceptions.base_exception import ResumeParserException


class FileParsingError(ResumeParserException):
    """Exception raised when file parsing fails."""


class FieldExtractionError(ResumeParserException):
    """Exception raised when field extraction fails."""


class UnsupportedFileFormatError(ResumeParserException):
    """Exception raised when file format is not supported."""


class InvalidConfigurationError(ResumeParserException):
    """Exception raised when configuration is invalid."""


class StrategyExtractionError(ResumeParserException):
    """Raised when a strategy fails to extract a field."""


class InvalidStrategyConfigError(ResumeParserException):
    """Raised when a strategy is configured incorrectly."""


class NoMatchFoundError(StrategyExtractionError):
    """Raised when no match is found by the strategy."""
