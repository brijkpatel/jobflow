"""Data model for extracted resume information."""

import json
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any


@dataclass
class ResumeData:
    """Data class representing extracted resume information.

    This class encapsulates the three key fields extracted from a resume:
    name, email, and skills. Fields can be None if extraction fails.

    Attributes:
        name: The candidate's full name (can be None if extraction failed)
        email: The candidate's email address (can be None if extraction failed)
        skills: List of technical/professional skills (can be empty if extraction failed)
    """

    name: Optional[str] = None
    email: Optional[str] = None
    skills: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the resume data to a dictionary.

        Returns:
            Dictionary representation of the resume data
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
        """String representation of the resume data."""
        return f"ResumeData(name='{self.name}', email='{self.email}', skills={self.skills})"

    def __repr__(self) -> str:
        """Detailed string representation for debugging."""
        return self.__str__()
