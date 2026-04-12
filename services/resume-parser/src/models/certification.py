"""Certification entry extracted from a resume."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class CertificationEntry:
    """A professional certification or license.

    Attributes:
        name: Certification name (e.g., "AWS Certified Solutions Architect")
        issuing_organization: Organization that issued it (e.g., "Amazon Web Services")
        issue_date: Date the certification was obtained
        expiry_date: Expiry date if applicable
        credential_id: Certificate or license ID number
        credential_url: Verification URL
    """

    name: str = ""
    issuing_organization: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None
