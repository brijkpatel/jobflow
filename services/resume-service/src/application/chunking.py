from __future__ import annotations

from datetime import UTC, datetime

from domain.models import ResumeChunk, ResumeData


def calculate_years_of_experience(resume: ResumeData) -> float | None:
    spans: list[tuple[datetime, datetime]] = []
    now = datetime.now(tz=UTC)
    for item in resume.experience:
        start = _parse_date(item.start_date)
        if start is None:
            continue
        end = _parse_date(item.end_date) if item.end_date else now
        if end >= start:
            spans.append((start, end))
    if not spans:
        return None
    total_days = sum((end - start).days for start, end in spans)
    return round(total_days / 365.25, 2)


def build_resume_chunks(resume: ResumeData) -> list[ResumeChunk]:
    chunks: list[ResumeChunk] = []
    pieces: list[tuple[str, str]] = []
    if resume.summary:
        pieces.append(("summary", resume.summary))
    if resume.skills:
        pieces.append(("skills", ", ".join(resume.skills)))
    for entry in resume.experience:
        text = "\n".join(
            part
            for part in [
                f"{entry.title} at {entry.company}",
                entry.location or "",
                "\n".join(entry.bullets),
            ]
            if part
        )
        pieces.append(("experience", text))
    for entry in resume.education:
        pieces.append(
            (
                "education",
                " - ".join(
                    part for part in [entry.degree, entry.field, entry.institution] if part
                ),
            )
        )
    for entry in resume.certifications:
        pieces.append(
            ("certification", " - ".join(part for part in [entry.name, entry.issuer] if part))
        )
    if resume.languages:
        pieces.append(("languages", ", ".join(resume.languages)))
    for entry in resume.projects:
        pieces.append(
            (
                "project",
                "\n".join(
                    part
                    for part in [
                        entry.name,
                        entry.description or "",
                        ", ".join(entry.technologies),
                    ]
                    if part
                ),
            )
        )
    for index, (section_type, text) in enumerate(pieces):
        if text.strip():
            chunks.append(ResumeChunk(section_type=section_type, text=text.strip(), chunk_index=index))
    return chunks


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m", "%Y"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=UTC)
        except ValueError:
            continue
    return None
