class ResumeServiceError(Exception):
    pass


class UnsupportedFileFormatError(ResumeServiceError):
    pass


class FileParsingError(ResumeServiceError):
    pass


class ExtractionError(ResumeServiceError):
    pass


class ExternalDependencyError(ResumeServiceError):
    pass
