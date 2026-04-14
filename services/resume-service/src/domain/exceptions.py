"""Domain exceptions for the resume-service."""

from __future__ import annotations

from typing import Optional


class ResumeServiceError(Exception):
    """Base exception for all resume-service errors."""

    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        self.message = message
        self.original_exception = original_exception
        super().__init__(self.message)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

class FileParsingError(ResumeServiceError):
    """Raised when file bytes cannot be parsed into text."""


class UnsupportedFileFormatError(ResumeServiceError):
    """Raised when the file extension / MIME type is not supported."""


# ---------------------------------------------------------------------------
# Extraction
# ---------------------------------------------------------------------------

class FieldExtractionError(ResumeServiceError):
    """Raised when field extraction fails at the coordinator level."""


class NoMatchFoundError(FieldExtractionError):
    """Raised by an extraction strategy when no value is found."""


class InvalidStrategyConfigError(ResumeServiceError):
    """Raised when an extraction strategy is misconfigured."""


# ---------------------------------------------------------------------------
# Infrastructure (surfaced to use cases via these domain exceptions)
# ---------------------------------------------------------------------------

class ExternalServiceError(ResumeServiceError):
    """Raised when an external service call (LLM, embeddings, OCI…) fails."""


class StorageFetchError(ResumeServiceError):
    """Raised when the OCI object cannot be retrieved."""


class EventPublishError(ResumeServiceError):
    """Raised when publishing to Kafka fails."""


class ResumeNotFoundError(ResumeServiceError):
    """Raised when a resume lookup returns no result."""
