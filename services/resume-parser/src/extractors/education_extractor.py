"""Extract education entries from resume text."""

from typing import List

from interfaces import FieldExtractor, ExtractionStrategy
from models.education import EducationEntry
from extractors.structured_extractor import StructuredExtractor


class EducationExtractor(StructuredExtractor[EducationEntry], FieldExtractor[List[EducationEntry]]):
    """Extract education entries using LLM structured output."""

    def __init__(self, extraction_strategy: ExtractionStrategy[List[str]]):
        StructuredExtractor.__init__(self, extraction_strategy)

    def _field_name(self) -> str:
        return "Education"

    def _parse_item(self, data: dict) -> EducationEntry:
        return EducationEntry(
            institution=data.get("institution") or "",
            degree=data.get("degree") or None,
            field_of_study=data.get("field_of_study") or None,
            start_date=data.get("start_date") or None,
            end_date=data.get("end_date") or None,
            gpa=_to_float(data.get("gpa")),
            honors=data.get("honors") or None,
        )


def _to_float(value) -> float | None:
    try:
        return float(value) if value is not None else None
    except (ValueError, TypeError):
        return None
