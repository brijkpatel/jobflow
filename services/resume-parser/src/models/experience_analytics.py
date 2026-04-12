"""Experience analytics computed from work history."""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class ExperienceAnalytics:
    """Computed analytics derived from work experience entries.

    Attributes:
        total_years: Total professional experience in years (float, rounded to 1dp)
        years_by_role: Years spent in each unique job title
                       e.g., {"Software Engineer": 3.5, "Tech Lead": 1.0}
        years_by_company: Years spent at each company
        skills_with_years: Estimated years of exposure per skill,
                           aggregated across all roles where the skill appears
                           e.g., {"Python": 4.5, "Docker": 2.0}
        most_recent_title: The most recent job title held
        career_level: Inferred seniority ("Junior", "Mid", "Senior", "Lead",
                      "Manager", "Director", "Executive")
    """

    total_years: float = 0.0
    years_by_role: Dict[str, float] = field(default_factory=dict)
    years_by_company: Dict[str, float] = field(default_factory=dict)
    skills_with_years: Dict[str, float] = field(default_factory=dict)
    most_recent_title: str = ""
    career_level: str = ""
