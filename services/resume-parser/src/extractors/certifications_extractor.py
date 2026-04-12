"""Extract certification entries from resume text."""

from typing import List

from interfaces import FieldExtractor, ExtractionStrategy
from models.certification import CertificationEntry
from extractors.structured_extractor import StructuredExtractor


class CertificationsExtractor(StructuredExtractor[CertificationEntry], FieldExtractor[List[CertificationEntry]]):
    """Extract certification entries using LLM structured output."""

    def __init__(self, extraction_strategy: ExtractionStrategy[List[str]]):
        StructuredExtractor.__init__(self, extraction_strategy)

    def _field_name(self) -> str:
        return "Certifications"

    def _parse_item(self, data: dict) -> CertificationEntry:
        return CertificationEntry(
            name=data.get("name") or "",
            issuing_organization=data.get("issuing_organization") or None,
            issue_date=data.get("issue_date") or None,
            expiry_date=data.get("expiry_date") or None,
            credential_id=data.get("credential_id") or None,
            credential_url=data.get("credential_url") or None,
        )
