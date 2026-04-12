"""Contact information extracted from a resume."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ContactInfo:
    """All contact-related information found on a resume.

    Attributes:
        phone: Primary phone number
        location: City, state, country or full address
        linkedin_url: LinkedIn profile URL
        github_url: GitHub profile URL
        portfolio_url: Personal website or portfolio URL
        other_urls: Any other URLs (Twitter, Behance, Dribbble, etc.)
    """

    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    other_urls: List[str] = field(default_factory=list)
