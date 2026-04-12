"""Orchestrates extraction of all fields from resume text."""

from typing import Dict, List, Any, Optional

from interfaces import FieldExtractor, FieldType
from models import (
    ResumeData,
    ContactInfo,
    WorkExperienceEntry,
    EducationEntry,
    CertificationEntry,
    ProjectEntry,
    SkillEntry,
    VolunteerEntry,
    PublicationEntry,
    ExperienceAnalytics,
)
from extractors.experience_analytics_extractor import ExperienceAnalyticsExtractor
from utils import logger


# Required fields — extraction is attempted for every resume
_REQUIRED_FIELDS = {FieldType.NAME, FieldType.EMAIL, FieldType.SKILLS}

# Optional fields — missing extractors are silently skipped
_OPTIONAL_FIELDS = {
    FieldType.PHONE,
    FieldType.LOCATION,
    FieldType.LINKEDIN_URL,
    FieldType.GITHUB_URL,
    FieldType.PORTFOLIO_URL,
    FieldType.OTHER_URLS,
    FieldType.SUMMARY,
    FieldType.WORK_EXPERIENCE,
    FieldType.EDUCATION,
    FieldType.CERTIFICATIONS,
    FieldType.PROJECTS,
    FieldType.INTERESTS,
    FieldType.LANGUAGES,
    FieldType.AWARDS,
    FieldType.VOLUNTEER_EXPERIENCE,
    FieldType.PUBLICATIONS,
}

# Fields that return lists (empty list default, not None)
_LIST_FIELDS = {
    FieldType.SKILLS,
    FieldType.OTHER_URLS,
    FieldType.WORK_EXPERIENCE,
    FieldType.EDUCATION,
    FieldType.CERTIFICATIONS,
    FieldType.PROJECTS,
    FieldType.INTERESTS,
    FieldType.LANGUAGES,
    FieldType.AWARDS,
    FieldType.VOLUNTEER_EXPERIENCE,
    FieldType.PUBLICATIONS,
}


class ResumeExtractor:
    """Runs multiple extractors for each field with automatic fallback.

    How it works:
        - NAME, EMAIL, and SKILLS are required — their extractors must be provided.
        - All other fields are optional — their extractors may be omitted.
        - For each field, extractors are tried in order until one succeeds.
        - If all extractors fail for a field, None (or [] for list fields) is returned.
        - After text extraction, experience analytics are computed from work history.

    Example:
        For email: tries Regex → NER → LLM
        If Regex succeeds, returns immediately; otherwise falls back in order.
    """

    def __init__(
        self,
        extractors: Dict[FieldType, List[FieldExtractor[Any]]],
        analytics_extractor: Optional[ExperienceAnalyticsExtractor] = None,
    ):
        """Initialize with extractors for each field type.

        Args:
            extractors: Dict mapping field types to ordered list of extractors.
                        Must include NAME, EMAIL, and SKILLS.
            analytics_extractor: Optional analytics extractor. If None, a default
                                  instance is created automatically.

        Raises:
            ValueError: If required fields are missing from extractors
        """
        if not extractors:
            raise ValueError("extractors dictionary cannot be None or empty")

        provided = set(extractors.keys())
        missing = _REQUIRED_FIELDS - provided
        if missing:
            raise ValueError(
                f"Missing required field types: {[f.value for f in missing]}"
            )

        self.extractors = extractors
        self.analytics_extractor = analytics_extractor or ExperienceAnalyticsExtractor()

        logger.info(
            f"ResumeExtractor initialized with extractors for "
            f"{len(extractors)} field types"
        )

    def extract(self, text: str) -> ResumeData:
        """Extract all configured fields from resume text.

        Steps:
            1. Validate text is not empty
            2. Extract each field via its extractor chain
            3. Assemble ContactInfo from individual contact fields
            4. Compute ExperienceAnalytics from work experience
            5. Return fully populated ResumeData

        Args:
            text: Resume text to extract from

        Returns:
            ResumeData with all extracted and computed fields

        Raises:
            ValueError: If text is empty
        """
        if not text or not text.strip():
            raise ValueError("Resume text cannot be empty")

        logger.info("Starting full field extraction from resume text")

        # --- Core fields ---
        name = self._extract_field(FieldType.NAME, text)
        email = self._extract_field(FieldType.EMAIL, text)
        skills = self._extract_field(FieldType.SKILLS, text)

        # --- Contact fields ---
        phone = self._extract_field(FieldType.PHONE, text)
        location = self._extract_field(FieldType.LOCATION, text)
        # URL extractors always return List[str]; single-URL fields keep only the first
        linkedin_url_raw = self._extract_field(FieldType.LINKEDIN_URL, text)
        github_url_raw   = self._extract_field(FieldType.GITHUB_URL, text)
        portfolio_url_raw = self._extract_field(FieldType.PORTFOLIO_URL, text)
        other_urls = self._extract_field(FieldType.OTHER_URLS, text) or []

        linkedin_url  = linkedin_url_raw[0] if linkedin_url_raw else None
        github_url    = github_url_raw[0]   if github_url_raw   else None
        portfolio_url = portfolio_url_raw[0] if portfolio_url_raw else None

        contact = ContactInfo(
            phone=phone,
            location=location,
            linkedin_url=linkedin_url,
            github_url=github_url,
            portfolio_url=portfolio_url,
            other_urls=other_urls,
        )

        # --- Professional narrative ---
        summary = self._extract_field(FieldType.SUMMARY, text)

        # --- Structured sections ---
        work_experience: Optional[List[WorkExperienceEntry]] = self._extract_field(
            FieldType.WORK_EXPERIENCE, text
        )
        education: Optional[List[EducationEntry]] = self._extract_field(
            FieldType.EDUCATION, text
        )
        certifications: Optional[List[CertificationEntry]] = self._extract_field(
            FieldType.CERTIFICATIONS, text
        )
        projects: Optional[List[ProjectEntry]] = self._extract_field(
            FieldType.PROJECTS, text
        )
        volunteer_experience: Optional[List[VolunteerEntry]] = self._extract_field(
            FieldType.VOLUNTEER_EXPERIENCE, text
        )
        publications: Optional[List[PublicationEntry]] = self._extract_field(
            FieldType.PUBLICATIONS, text
        )

        # --- Personal ---
        interests: Optional[List[str]] = self._extract_field(FieldType.INTERESTS, text)
        languages: Optional[List[str]] = self._extract_field(FieldType.LANGUAGES, text)
        awards: Optional[List[str]] = self._extract_field(FieldType.AWARDS, text)

        # --- Computed analytics ---
        experience_analytics: Optional[ExperienceAnalytics] = None
        if work_experience:
            try:
                experience_analytics = self.analytics_extractor.compute(work_experience)
                logger.info(
                    f"Computed experience analytics: "
                    f"{experience_analytics.total_years} total years, "
                    f"level={experience_analytics.career_level}"
                )
            except Exception as e:
                logger.error(f"Experience analytics computation failed: {e}")

        resume_data = ResumeData(
            name=name,
            email=email,
            skills=skills,
            contact=contact,
            summary=summary,
            work_experience=work_experience,
            education=education,
            certifications=certifications,
            projects=projects,
            interests=interests,
            languages=languages,
            awards=awards,
            volunteer_experience=volunteer_experience,
            publications=publications,
            experience_analytics=experience_analytics,
        )

        logger.info(f"Extraction complete: {resume_data}")
        return resume_data

    def _extract_field(self, field_type: FieldType, text: str) -> Optional[Any]:
        """Try extractors in order until one succeeds.

        Args:
            field_type: Field to extract
            text: Resume text

        Returns:
            Extracted value, or None/[] if all extractors fail or none configured
        """
        extractors = self.extractors.get(field_type, [])
        field_name = field_type.value

        if not extractors:
            # Optional field with no configured extractors
            return [] if field_type in _LIST_FIELDS else None

        logger.debug(
            f"Attempting to extract '{field_name}' using {len(extractors)} extractor(s)"
        )

        for idx, extractor in enumerate(extractors, 1):
            try:
                logger.debug(
                    f"Trying extractor {idx}/{len(extractors)} for '{field_name}'"
                )
                result = extractor.extract(text)

                if result is not None and result != [] and result != "":
                    logger.info(
                        f"Successfully extracted '{field_name}' via "
                        f"{extractor.__class__.__name__}"
                    )
                    return result
                else:
                    logger.warning(
                        f"Extractor {idx} returned empty result for '{field_name}'"
                    )
            except Exception as e:
                logger.error(
                    f"Extractor {idx} failed for '{field_name}': "
                    f"{type(e).__name__}: {e}"
                )
                continue

        logger.error(
            f"All {len(extractors)} extractor(s) failed for '{field_name}'. "
            f"Returning default."
        )
        return [] if field_type in _LIST_FIELDS else None
