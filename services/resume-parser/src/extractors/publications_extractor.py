"""Extract publication entries from resume text."""

from typing import List

from interfaces import FieldExtractor, ExtractionStrategy
from models.publication import PublicationEntry
from extractors.structured_extractor import StructuredExtractor


class PublicationsExtractor(StructuredExtractor[PublicationEntry], FieldExtractor[List[PublicationEntry]]):
    """Extract publication entries using LLM structured output."""

    def __init__(self, extraction_strategy: ExtractionStrategy[List[str]]):
        StructuredExtractor.__init__(self, extraction_strategy)

    def _field_name(self) -> str:
        return "Publications"

    def _parse_item(self, data: dict) -> PublicationEntry:
        return PublicationEntry(
            title=data.get("title") or "",
            publisher=data.get("publisher") or None,
            date=data.get("date") or None,
            url=data.get("url") or None,
            description=data.get("description") or None,
        )
