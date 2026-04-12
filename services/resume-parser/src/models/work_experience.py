"""Work experience entry extracted from a resume."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class WorkExperienceEntry:
    """A single work experience entry in chronological order.

    Attributes:
        company: Employer / organization name
        title: Job title / position
        location: Office location (city, remote, etc.)
        start_date: Start date as a string (e.g., "Jan 2020", "2020-01")
        end_date: End date or "Present"
        duration_months: Calculated duration in months (None if dates unavailable)
        description: Role summary or overview
        responsibilities: Bullet-point list of responsibilities/achievements
        skills_used: Technologies and skills explicitly mentioned in this role
    """

    company: str = ""
    title: str = ""
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration_months: Optional[int] = None
    description: Optional[str] = None
    responsibilities: List[str] = field(default_factory=list)
    skills_used: List[str] = field(default_factory=list)
