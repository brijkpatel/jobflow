"""Enriched skill entry with category and estimated proficiency."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SkillEntry:
    """A skill with metadata inferred from the resume.

    Attributes:
        name: Skill name (e.g., "Python", "Team Leadership")
        category: Skill category (e.g., "Programming Language", "Framework",
                  "Cloud Platform", "Soft Skill", "Tool", "Database", "DevOps")
        estimated_years: Estimated years of experience inferred from work history
        proficiency: Estimated proficiency level based on years
                     ("Beginner" <1yr, "Intermediate" 1-3yr, "Advanced" 3-6yr,
                      "Expert" >6yr)
    """

    name: str = ""
    category: Optional[str] = None
    estimated_years: Optional[float] = None
    proficiency: Optional[str] = None
