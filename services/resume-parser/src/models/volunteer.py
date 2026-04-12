"""Volunteer experience entry extracted from a resume."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class VolunteerEntry:
    """A single volunteer or community involvement entry.

    Attributes:
        organization: Organization or cause name
        role: Volunteer role or title
        start_date: Start date string
        end_date: End date string or "Present"
        description: Summary of contributions
        responsibilities: Specific tasks or achievements
    """

    organization: str = ""
    role: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    responsibilities: List[str] = field(default_factory=list)
