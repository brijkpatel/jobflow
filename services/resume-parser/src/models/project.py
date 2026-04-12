"""Project entry extracted from a resume."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ProjectEntry:
    """A personal or professional project.

    Attributes:
        name: Project name
        description: What the project does / its purpose
        technologies: Stack/tools used in the project
        url: Live URL, GitHub link, or any project link
        start_date: Project start date string
        end_date: Project end date string or "Present"
    """

    name: str = ""
    description: Optional[str] = None
    technologies: List[str] = field(default_factory=list)
    url: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
