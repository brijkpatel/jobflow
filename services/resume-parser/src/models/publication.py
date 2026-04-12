"""Publication entry extracted from a resume."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PublicationEntry:
    """A published article, paper, book, or other work.

    Attributes:
        title: Publication title
        publisher: Journal, conference, or publisher name
        date: Publication date string
        url: Link to the publication
        description: Brief summary or abstract
    """

    title: str = ""
    publisher: Optional[str] = None
    date: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
