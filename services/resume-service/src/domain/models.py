"""Domain models for the resume-service.

All models are plain dataclasses — zero framework imports.
Serialisation is an infrastructure concern; no to_dict / to_json here.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Contact
# ---------------------------------------------------------------------------

@dataclass
class ContactInfo:
    """All contact-related information found on a resume."""

    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    other_urls: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Work experience
# ---------------------------------------------------------------------------

@dataclass
class WorkExperienceEntry:
    """A single work experience entry."""

    company: str = ""
    title: str = ""
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration_months: Optional[int] = None
    description: Optional[str] = None
    responsibilities: List[str] = field(default_factory=list)
    skills_used: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Education
# ---------------------------------------------------------------------------

@dataclass
class EducationEntry:
    """A single education entry."""

    institution: str = ""
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    gpa: Optional[float] = None
    honors: Optional[str] = None


# ---------------------------------------------------------------------------
# Certifications
# ---------------------------------------------------------------------------

@dataclass
class CertificationEntry:
    """A professional certification or license."""

    name: str = ""
    issuing_organization: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

@dataclass
class ProjectEntry:
    """A personal or professional project."""

    name: str = ""
    description: Optional[str] = None
    technologies: List[str] = field(default_factory=list)
    url: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


# ---------------------------------------------------------------------------
# Enriched skills
# ---------------------------------------------------------------------------

@dataclass
class SkillEntry:
    """A skill with metadata inferred from the resume."""

    name: str = ""
    category: Optional[str] = None
    estimated_years: Optional[float] = None
    proficiency: Optional[str] = None


# ---------------------------------------------------------------------------
# Volunteer + publications
# ---------------------------------------------------------------------------

@dataclass
class VolunteerEntry:
    """A single volunteer or community involvement entry."""

    organization: str = ""
    role: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    responsibilities: List[str] = field(default_factory=list)


@dataclass
class PublicationEntry:
    """A published article, paper, book, or other work."""

    title: str = ""
    publisher: Optional[str] = None
    date: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None


# ---------------------------------------------------------------------------
# Experience analytics (computed, not stored directly)
# ---------------------------------------------------------------------------

@dataclass
class ExperienceAnalytics:
    """Computed analytics derived from work experience entries."""

    total_years: float = 0.0
    years_by_role: Dict[str, float] = field(default_factory=dict)
    years_by_company: Dict[str, float] = field(default_factory=dict)
    skills_with_years: Dict[str, float] = field(default_factory=dict)
    most_recent_title: str = ""
    career_level: str = ""


# ---------------------------------------------------------------------------
# Aggregate root
# ---------------------------------------------------------------------------

@dataclass
class ResumeData:
    """Complete structured representation of all data extracted from a resume.

    Identity fields (resume_id, user_id, tenant_id) are required for all
    persisted resumes. created_at is set at save time by the repository.

    Core fields (name, email, skills) are always attempted. All other fields
    are optional and may be None or empty if not present on the resume.
    """

    # Identity — required for persistence
    resume_id: uuid.UUID = field(default_factory=uuid.uuid4)
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    tenant_id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: Optional[datetime] = None

    # Storage reference — OCI Object Storage path for re-parse
    storage_object: Optional[str] = None

    # Core fields
    name: Optional[str] = None
    email: Optional[str] = None
    skills: Optional[List[str]] = None

    # Contact information
    contact: Optional[ContactInfo] = None

    # Professional narrative
    summary: Optional[str] = None

    # Structured history
    work_experience: Optional[List[WorkExperienceEntry]] = None
    education: Optional[List[EducationEntry]] = None
    certifications: Optional[List[CertificationEntry]] = None
    projects: Optional[List[ProjectEntry]] = None

    # Enriched skills (computed from work history + raw skills)
    enriched_skills: Optional[List[SkillEntry]] = None

    # Personal
    interests: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    awards: Optional[List[str]] = None

    # Optional sections
    volunteer_experience: Optional[List[VolunteerEntry]] = None
    publications: Optional[List[PublicationEntry]] = None

    # Computed analytics (derived from work_experience)
    experience_analytics: Optional[ExperienceAnalytics] = None

    def __str__(self) -> str:
        exp_count = len(self.work_experience) if self.work_experience else 0
        skills_count = len(self.skills) if self.skills else 0
        total_yrs = (
            self.experience_analytics.total_years
            if self.experience_analytics
            else "?"
        )
        return (
            f"ResumeData(resume_id={self.resume_id}, name='{self.name}', "
            f"tenant_id={self.tenant_id}, skills={skills_count}, "
            f"experience_entries={exp_count}, total_years={total_yrs})"
        )

    def __repr__(self) -> str:
        return self.__str__()


# ---------------------------------------------------------------------------
# Chunk value object — for vector embeddings
# ---------------------------------------------------------------------------

@dataclass
class ResumeChunk:
    """A text chunk derived from a resume section, ready for embedding.

    No embedding field — embeddings are paired with chunks in the
    infrastructure layer via ResumeChunkVector and never stored on the domain
    object. This keeps the domain layer free of ML infrastructure concerns.
    """

    chunk_id: uuid.UUID = field(default_factory=uuid.uuid4)
    resume_id: uuid.UUID = field(default_factory=uuid.uuid4)
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    section: str = ""   # e.g. "summary", "work_experience", "skills"
    text: str = ""
