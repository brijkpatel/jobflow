"""Extract work experience entries from resume text."""

from typing import List

from interfaces import FieldExtractor, ExtractionStrategy
from models.work_experience import WorkExperienceEntry
from extractors.structured_extractor import StructuredExtractor


class WorkExperienceExtractor(StructuredExtractor[WorkExperienceEntry], FieldExtractor[List[WorkExperienceEntry]]):
    """Extract chronological work experience entries using LLM structured output."""

    def __init__(self, extraction_strategy: ExtractionStrategy[List[str]]):
        StructuredExtractor.__init__(self, extraction_strategy)

    def _field_name(self) -> str:
        return "WorkExperience"

    def _parse_item(self, data: dict) -> WorkExperienceEntry:
        return WorkExperienceEntry(
            company=data.get("company") or "",
            title=data.get("title") or "",
            location=data.get("location") or None,
            start_date=data.get("start_date") or None,
            end_date=data.get("end_date") or None,
            duration_months=_to_int(data.get("duration_months")),
            description=data.get("description") or None,
            responsibilities=_to_str_list(data.get("responsibilities")),
            skills_used=_to_str_list(data.get("skills_used")),
        )


def _to_int(value) -> int | None:
    try:
        return int(value) if value is not None else None
    except (ValueError, TypeError):
        return None


def _to_str_list(value) -> List[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if v]
    return []
