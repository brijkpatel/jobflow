from __future__ import annotations

from typing import Any

from domain.interfaces import ExtractionStrategy, LLMClient
from domain.models import Certification, Education, Experience, Project, ResumeData


class ResumeExtractionOrchestrator:
    def __init__(
        self,
        *,
        llm_client: LLMClient,
        simple_field_strategies: dict[str, list[ExtractionStrategy[Any]]],
        llm_fields: list[str] | None = None,
    ) -> None:
        self._llm_client = llm_client
        self._simple_field_strategies = simple_field_strategies
        self._llm_fields = llm_fields or [
            "name",
            "summary",
            "skills",
            "experience",
            "education",
            "certifications",
            "languages",
            "projects",
        ]

    async def extract(self, text: str) -> ResumeData:
        simple = {
            field: self._extract_with_fallback(field, text)
            for field in self._simple_field_strategies
        }
        llm_payload = await self._llm_client.extract_fields(text, self._llm_fields)
        return ResumeData(
            name=(simple.get("name") or llm_payload.get("name")),
            email=simple.get("email"),
            phone=simple.get("phone"),
            location=simple.get("location"),
            linkedin_url=simple.get("linkedin_url"),
            github_url=simple.get("github_url"),
            portfolio_url=simple.get("portfolio_url"),
            summary=_first_string(llm_payload.get("summary")),
            skills=_string_list(llm_payload.get("skills")),
            experience=_experience_list(llm_payload.get("experience")),
            education=_education_list(llm_payload.get("education")),
            certifications=_certification_list(llm_payload.get("certifications")),
            languages=_string_list(llm_payload.get("languages")),
            projects=_project_list(llm_payload.get("projects")),
        )

    def _extract_with_fallback(self, field: str, text: str) -> Any:
        for strategy in self._simple_field_strategies.get(field, []):
            value = strategy.extract(text)
            if value in (None, "", []):
                continue
            if isinstance(value, list):
                return value[0]
            return value
        return None


def _first_string(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, list) and value:
        first = value[0]
        return first.strip() if isinstance(first, str) and first.strip() else None
    return None


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _experience_list(value: Any) -> list[Experience]:
    if not isinstance(value, list):
        return []
    return [
        Experience(
            company=str(item.get("company", "")),
            title=str(item.get("title", "")),
            start_date=str(item.get("start_date", "")),
            end_date=item.get("end_date"),
            location=item.get("location"),
            bullets=_string_list(item.get("bullets")),
        )
        for item in value
        if isinstance(item, dict)
    ]


def _education_list(value: Any) -> list[Education]:
    if not isinstance(value, list):
        return []
    return [
        Education(
            institution=str(item.get("institution", "")),
            degree=str(item.get("degree", "")),
            field=item.get("field"),
            graduation_date=item.get("graduation_date"),
            gpa=float(item["gpa"]) if item.get("gpa") is not None else None,
        )
        for item in value
        if isinstance(item, dict)
    ]


def _certification_list(value: Any) -> list[Certification]:
    if not isinstance(value, list):
        return []
    return [
        Certification(
            name=str(item.get("name", "")),
            issuer=item.get("issuer"),
            date=item.get("date"),
        )
        for item in value
        if isinstance(item, dict)
    ]


def _project_list(value: Any) -> list[Project]:
    if not isinstance(value, list):
        return []
    return [
        Project(
            name=str(item.get("name", "")),
            description=item.get("description"),
            technologies=_string_list(item.get("technologies")),
        )
        for item in value
        if isinstance(item, dict)
    ]
