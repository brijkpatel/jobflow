from exceptions.base_exception import ResumeParserException


class ExternalServiceError(ResumeParserException):
    """Raised when an external service (like LLM API, Gliner, etc.) fails."""
