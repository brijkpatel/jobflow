"""Education entry extracted from a resume."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class EducationEntry:
    """A single education entry.

    Attributes:
        institution: University, college, or school name
        degree: Degree type (e.g., "Bachelor of Science", "MBA")
        field_of_study: Major or concentration (e.g., "Computer Science")
        start_date: Enrollment start date string
        end_date: Graduation date string or "Present"
        gpa: Grade point average if mentioned
        honors: Honors, distinctions, or awards (e.g., "Cum Laude")
    """

    institution: str = ""
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    gpa: Optional[float] = None
    honors: Optional[str] = None
