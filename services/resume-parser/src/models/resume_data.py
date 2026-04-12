"""Data model for extracted resume information."""

import json
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Any

from models.contact_info import ContactInfo
from models.work_experience import WorkExperienceEntry
from models.education import EducationEntry
from models.certification import CertificationEntry
from models.project import ProjectEntry
from models.skill_entry import SkillEntry
from models.volunteer import VolunteerEntry
from models.publication import PublicationEntry
from models.experience_analytics import ExperienceAnalytics


@dataclass
class ResumeData:
    """Complete structured representation of all data extracted from a resume.

    Core fields (name, email, skills) are always attempted. All other fields
    are optional and may be None or empty if not present on the resume or if
    extraction fails.

    Attributes:
        name: Candidate's full name
        email: Primary email address
        skills: Raw skill list extracted directly from the resume text
        contact: All contact information (phone, location, social URLs)
        summary: Professional summary or objective statement
        work_experience: Chronological list of work experience entries
        education: List of education entries
        certifications: Professional certifications and licenses
        projects: Personal or professional projects
        enriched_skills: Skills with category, estimated years, and proficiency
        interests: Hobbies and personal interests
        languages: Spoken/written languages
        awards: Awards and achievements
        volunteer_experience: Volunteer and community involvement
        publications: Published works
        experience_analytics: Computed analytics from work history
    """

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

    def to_dict(self) -> Dict[str, Any]:
        """Convert the resume data to a nested dictionary.

        Returns:
            Fully nested dictionary representation (all dataclasses expanded)
        """
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Convert the resume data to a JSON string.

        Args:
            indent: Number of spaces for JSON indentation (default: 2)

        Returns:
            JSON string representation of the resume data
        """
        return json.dumps(self.to_dict(), indent=indent)

    def __str__(self) -> str:
        """Concise string representation."""
        exp_count = len(self.work_experience) if self.work_experience else 0
        skills_count = len(self.skills) if self.skills else 0
        total_yrs = (
            self.experience_analytics.total_years
            if self.experience_analytics
            else "?"
        )
        return (
            f"ResumeData(name='{self.name}', email='{self.email}', "
            f"skills={skills_count}, experience_entries={exp_count}, "
            f"total_years={total_yrs})"
        )

    def __repr__(self) -> str:
        """Detailed string representation for debugging."""
        return self.__str__()
