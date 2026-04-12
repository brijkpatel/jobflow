"""Extract project entries from resume text."""

from typing import List

from interfaces import FieldExtractor, ExtractionStrategy
from models.project import ProjectEntry
from extractors.structured_extractor import StructuredExtractor


class ProjectsExtractor(StructuredExtractor[ProjectEntry], FieldExtractor[List[ProjectEntry]]):
    """Extract project entries using LLM structured output."""

    def __init__(self, extraction_strategy: ExtractionStrategy[List[str]]):
        StructuredExtractor.__init__(self, extraction_strategy)

    def _field_name(self) -> str:
        return "Projects"

    def _parse_item(self, data: dict) -> ProjectEntry:
        return ProjectEntry(
            name=data.get("name") or "",
            description=data.get("description") or None,
            technologies=_to_str_list(data.get("technologies")),
            url=data.get("url") or None,
            start_date=data.get("start_date") or None,
            end_date=data.get("end_date") or None,
        )


def _to_str_list(value) -> List[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if v]
    return []
