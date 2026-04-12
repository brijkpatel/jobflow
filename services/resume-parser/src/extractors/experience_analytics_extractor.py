"""Compute experience analytics from parsed work experience entries."""

import re
from datetime import date
from typing import Dict, List, Optional, Tuple

from interfaces import ComputedFieldExtractor
from models.work_experience import WorkExperienceEntry
from models.experience_analytics import ExperienceAnalytics
from utils import logger

# Ordered seniority keywords for career-level inference
_SENIORITY_LEVELS = [
    ("Executive", {"cto", "ceo", "coo", "ciso", "chief", "president", "vp", "vice president"}),
    ("Director", {"director", "head of"}),
    ("Manager", {"manager", "lead", "principal", "staff"}),
    ("Senior", {"senior", "sr.", "sr "}),
    ("Mid", {"mid", "ii", "iii", "2", "3"}),
    ("Junior", {"junior", "jr.", "jr ", "entry", "associate", "intern", "trainee"}),
]

# Short month abbreviations → month number
_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    "january": 1, "february": 2, "march": 3, "april": 4, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10,
    "november": 11, "december": 12,
}


class ExperienceAnalyticsExtractor(ComputedFieldExtractor[ExperienceAnalytics, List[WorkExperienceEntry]]):
    """Derive analytics from a list of WorkExperienceEntry objects.

    Computes:
    - Total professional experience in years
    - Years spent in each unique job title
    - Years spent at each company
    - Estimated years per skill (aggregated across roles)
    - Most recent job title
    - Inferred career seniority level
    """

    def compute(self, data: List[WorkExperienceEntry]) -> ExperienceAnalytics:
        """Compute analytics from the provided work experience list.

        Args:
            data: List of WorkExperienceEntry (typically reverse-chronological)

        Returns:
            ExperienceAnalytics with all computed fields
        """
        if not data:
            logger.debug("No work experience provided; returning empty analytics")
            return ExperienceAnalytics()

        total_months = 0
        years_by_role: Dict[str, float] = {}
        years_by_company: Dict[str, float] = {}
        skills_months: Dict[str, float] = {}

        for entry in data:
            months = self._resolve_duration(entry)
            years = months / 12.0

            # Accumulate per-role and per-company
            if entry.title:
                years_by_role[entry.title] = round(
                    years_by_role.get(entry.title, 0.0) + years, 1
                )
            if entry.company:
                years_by_company[entry.company] = round(
                    years_by_company.get(entry.company, 0.0) + years, 1
                )

            # Accumulate per-skill
            for skill in entry.skills_used:
                skill_key = skill.strip()
                if skill_key:
                    skills_months[skill_key] = skills_months.get(skill_key, 0.0) + months

            total_months += months

        total_years = round(total_months / 12.0, 1)
        skills_with_years = {
            skill: round(months / 12.0, 1)
            for skill, months in skills_months.items()
        }

        most_recent_title = data[0].title if data else ""
        career_level = self._infer_career_level(most_recent_title, total_years)

        return ExperienceAnalytics(
            total_years=total_years,
            years_by_role=years_by_role,
            years_by_company=years_by_company,
            skills_with_years=skills_with_years,
            most_recent_title=most_recent_title,
            career_level=career_level,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _resolve_duration(self, entry: WorkExperienceEntry) -> int:
        """Return the duration in months for one work entry.

        Priority order:
        1. Use entry.duration_months if already set (provided by LLM)
        2. Parse start_date / end_date strings
        3. Return 0 if nothing is available
        """
        if entry.duration_months is not None and entry.duration_months > 0:
            return entry.duration_months

        start = self._parse_date(entry.start_date)
        end = self._parse_date(entry.end_date, default_today=True)

        if start and end and end >= start:
            return (end.year - start.year) * 12 + (end.month - start.month)

        logger.debug(
            f"Could not determine duration for '{entry.title}' at '{entry.company}'"
        )
        return 0

    @staticmethod
    def _parse_date(date_str: Optional[str], default_today: bool = False) -> Optional[date]:
        """Try to parse a loose date string into a date object.

        Handles:
        - "Present", "Current", "Now" → today (when default_today=True)
        - "2023", "2023-01", "Jan 2023", "January 2023", "01/2023"
        """
        if not date_str:
            return date.today() if default_today else None

        normalised = date_str.strip().lower()

        if normalised in {"present", "current", "now", "today", "-"}:
            return date.today()

        # Try ISO YYYY-MM-DD
        m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", normalised)
        if m:
            try:
                return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except ValueError:
                pass

        # Try YYYY-MM
        m = re.match(r"^(\d{4})-(\d{2})$", normalised)
        if m:
            try:
                return date(int(m.group(1)), int(m.group(2)), 1)
            except ValueError:
                pass

        # Try MM/YYYY or MM-YYYY
        m = re.match(r"^(\d{1,2})[/\-](\d{4})$", normalised)
        if m:
            try:
                return date(int(m.group(2)), int(m.group(1)), 1)
            except ValueError:
                pass

        # Try "Month YYYY" or "Mon YYYY"
        m = re.match(r"^([a-z]+)\.?\s+(\d{4})$", normalised)
        if m:
            month_num = _MONTHS.get(m.group(1))
            if month_num:
                try:
                    return date(int(m.group(2)), month_num, 1)
                except ValueError:
                    pass

        # Try bare year "YYYY"
        m = re.match(r"^(\d{4})$", normalised)
        if m:
            try:
                return date(int(m.group(1)), 1, 1)
            except ValueError:
                pass

        return None

    @staticmethod
    def _infer_career_level(title: str, total_years: float) -> str:
        """Infer career level from the most recent job title and total years.

        Uses token-based matching to avoid false substring matches (e.g.
        "cto" inside "director").  Multi-word keywords ("head of",
        "vice president") are matched as phrases against the full lowercased
        title; single-word keywords are matched against the set of word
        tokens extracted from the title.
        """
        if not title:
            return _years_to_level(total_years)

        title_lower = title.lower()
        # Build a set of clean word tokens (strip punctuation)
        word_tokens = set(re.sub(r"[^\w\s]", " ", title_lower).split())

        for level, keywords in _SENIORITY_LEVELS:
            for kw in keywords:
                kw_clean = kw.strip().rstrip(".")
                if " " in kw_clean:
                    # Multi-word phrase: substring check against full title
                    if kw_clean in title_lower:
                        return level
                else:
                    # Single word: exact token match to avoid false positives
                    if kw_clean in word_tokens:
                        return level

        return _years_to_level(total_years)


def _years_to_level(years: float) -> str:
    """Fall-back seniority inference based solely on years of experience."""
    if years < 1:
        return "Junior"
    if years < 3:
        return "Mid"
    if years < 6:
        return "Senior"
    if years < 10:
        return "Lead"
    return "Executive"
