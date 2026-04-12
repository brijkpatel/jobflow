from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Experience:
    company: str
    title: str
    start_date: str
    end_date: str | None = None
    location: str | None = None
    bullets: list[str] = field(default_factory=list)


@dataclass
class Education:
    institution: str
    degree: str
    field: str | None = None
    graduation_date: str | None = None
    gpa: float | None = None


@dataclass
class Certification:
    name: str
    issuer: str | None = None
    date: str | None = None


@dataclass
class Project:
    name: str
    description: str | None = None
    technologies: list[str] = field(default_factory=list)


@dataclass
class ResumeChunk:
    section_type: str
    text: str
    chunk_index: int
    embedding: list[float] | None = None


@dataclass
class ResumeData:
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    summary: str | None = None
    skills: list[str] = field(default_factory=list)
    experience: list[Experience] = field(default_factory=list)
    education: list[Education] = field(default_factory=list)
    certifications: list[Certification] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    projects: list[Project] = field(default_factory=list)
    years_of_experience: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ResumeData":
        return cls(
            name=payload.get("name"),
            email=payload.get("email"),
            phone=payload.get("phone"),
            location=payload.get("location"),
            linkedin_url=payload.get("linkedin_url"),
            github_url=payload.get("github_url"),
            portfolio_url=payload.get("portfolio_url"),
            summary=payload.get("summary"),
            skills=list(payload.get("skills", [])),
            experience=[Experience(**item) for item in payload.get("experience", [])],
            education=[Education(**item) for item in payload.get("education", [])],
            certifications=[
                Certification(**item) for item in payload.get("certifications", [])
            ],
            languages=list(payload.get("languages", [])),
            projects=[Project(**item) for item in payload.get("projects", [])],
            years_of_experience=payload.get("years_of_experience"),
        )


@dataclass
class ResumeRecord:
    resume_id: str
    tenant_id: str
    user_id: str
    resume: ResumeData


@dataclass
class ParseResumeResult:
    resume_id: str
    resume: ResumeData
    chunks: list[ResumeChunk] = field(default_factory=list)
