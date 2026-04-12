from typing import Optional


class ResumeParserException(Exception):
    """Base exception class for resume parser framework."""

    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        """Initialize the exception.

        Args:
            message: Human-readable error message
            original_exception: Optional original exception that caused this error
        """
        self.message = message
        self.original_exception = original_exception
        super().__init__(self.message)
