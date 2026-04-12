"""Extract volunteer experience entries from resume text."""

from typing import List

from interfaces import FieldExtractor, ExtractionStrategy
from models.volunteer import VolunteerEntry
from extractors.structured_extractor import StructuredExtractor


class VolunteerExtractor(StructuredExtractor[VolunteerEntry], FieldExtractor[List[VolunteerEntry]]):
    """Extract volunteer experience entries using LLM structured output."""

    def __init__(self, extraction_strategy: ExtractionStrategy[List[str]]):
        StructuredExtractor.__init__(self, extraction_strategy)

    def _field_name(self) -> str:
        return "VolunteerExperience"

    def _parse_item(self, data: dict) -> VolunteerEntry:
        return VolunteerEntry(
            organization=data.get("organization") or "",
            role=data.get("role") or None,
            start_date=data.get("start_date") or None,
            end_date=data.get("end_date") or None,
            description=data.get("description") or None,
            responsibilities=_to_str_list(data.get("responsibilities")),
        )


def _to_str_list(value) -> List[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if v]
    return []
