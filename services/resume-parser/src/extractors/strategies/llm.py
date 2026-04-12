"""Extract fields using Large Language Models (Gemini)."""

import json
import os
from typing import List
import google.generativeai as genai  # type: ignore

from interfaces import ExtractionStrategy, FieldSpec, FieldType
from exceptions import (
    InvalidStrategyConfigError,
    NoMatchFoundError,
    ExternalServiceError,
)

# Fields that return an array of JSON-object strings rather than plain strings.
_STRUCTURED_FIELD_TYPES = {
    FieldType.WORK_EXPERIENCE,
    FieldType.EDUCATION,
    FieldType.CERTIFICATIONS,
    FieldType.PROJECTS,
    FieldType.VOLUNTEER_EXPERIENCE,
    FieldType.PUBLICATIONS,
}

# JSON schema hints sent to the LLM for each structured field.
_STRUCTURED_SCHEMAS: dict = {
    FieldType.WORK_EXPERIENCE: (
        '{"company": "string", "title": "string", "location": "string|null", '
        '"start_date": "string|null", "end_date": "string|null", '
        '"duration_months": number|null, "description": "string|null", '
        '"responsibilities": ["string", ...], "skills_used": ["string", ...]}'
    ),
    FieldType.EDUCATION: (
        '{"institution": "string", "degree": "string|null", '
        '"field_of_study": "string|null", "start_date": "string|null", '
        '"end_date": "string|null", "gpa": number|null, "honors": "string|null"}'
    ),
    FieldType.CERTIFICATIONS: (
        '{"name": "string", "issuing_organization": "string|null", '
        '"issue_date": "string|null", "expiry_date": "string|null", '
        '"credential_id": "string|null", "credential_url": "string|null"}'
    ),
    FieldType.PROJECTS: (
        '{"name": "string", "description": "string|null", '
        '"technologies": ["string", ...], "url": "string|null", '
        '"start_date": "string|null", "end_date": "string|null"}'
    ),
    FieldType.VOLUNTEER_EXPERIENCE: (
        '{"organization": "string", "role": "string|null", '
        '"start_date": "string|null", "end_date": "string|null", '
        '"description": "string|null", "responsibilities": ["string", ...]}'
    ),
    FieldType.PUBLICATIONS: (
        '{"title": "string", "publisher": "string|null", '
        '"date": "string|null", "url": "string|null", "description": "string|null"}'
    ),
}

# Prompt instructions for every supported field type.
_FIELD_INSTRUCTIONS: dict = {
    FieldType.NAME: (
        "Extract the person's full name from the resume. "
        "Return a JSON array with a single string: [\"Full Name\"]. "
        "If not found return []."
    ),
    FieldType.EMAIL: (
        "Extract the primary email address from the resume. "
        "Return a JSON array with a single string: [\"email@example.com\"]. "
        "If not found return []."
    ),
    FieldType.SKILLS: (
        "Extract ALL technical and professional skills explicitly mentioned. "
        "Include programming languages, frameworks, tools, platforms, methodologies, "
        "and soft skills. Return a JSON array of strings. If none found return []."
    ),
    FieldType.PHONE: (
        "Extract the primary phone number. "
        "Return a JSON array with a single string in the original format. "
        "If not found return []."
    ),
    FieldType.LOCATION: (
        "Extract the person's current location (city, state, country or full address). "
        "Return a JSON array with a single string. If not found return []."
    ),
    FieldType.LINKEDIN_URL: (
        "Extract the LinkedIn profile URL. "
        "Return a JSON array with a single string. If not found return []."
    ),
    FieldType.GITHUB_URL: (
        "Extract the GitHub profile URL. "
        "Return a JSON array with a single string. If not found return []."
    ),
    FieldType.PORTFOLIO_URL: (
        "Extract the personal website or portfolio URL (not LinkedIn, not GitHub). "
        "Return a JSON array with a single string. If not found return []."
    ),
    FieldType.OTHER_URLS: (
        "Extract any other URLs from the resume that are NOT LinkedIn, GitHub, or a "
        "personal portfolio (e.g., Twitter, Behance, Dribbble, Kaggle, StackOverflow). "
        "Return a JSON array of strings. If none found return []."
    ),
    FieldType.SUMMARY: (
        "Extract the professional summary, objective, or profile statement verbatim. "
        "Return a JSON array with a single string. If not found return []."
    ),
    FieldType.WORK_EXPERIENCE: (
        "Extract ALL work experience entries in reverse chronological order "
        "(most recent first).\n"
        "For duration_months: calculate from start_date and end_date "
        "(use today for 'Present'). Set to null if dates are missing.\n"
        "For skills_used: list technologies/skills explicitly mentioned in each role.\n"
    ),
    FieldType.EDUCATION: (
        "Extract ALL education entries (degrees, diplomas, certificates from "
        "academic institutions) in reverse chronological order.\n"
        "For gpa: extract as a number (e.g., 3.8). Set to null if not mentioned.\n"
    ),
    FieldType.CERTIFICATIONS: (
        "Extract ALL professional certifications and licenses "
        "(NOT academic degrees — those go in education).\n"
    ),
    FieldType.PROJECTS: (
        "Extract ALL personal or professional projects listed on the resume.\n"
        "For technologies: list all tools/languages/frameworks mentioned per project.\n"
    ),
    FieldType.INTERESTS: (
        "Extract hobbies, personal interests, and extracurricular activities. "
        "Return a JSON array of strings. If none found return []."
    ),
    FieldType.LANGUAGES: (
        "Extract spoken or written languages (e.g., English, Spanish, Mandarin). "
        "Include proficiency level if mentioned (e.g., 'Spanish (Fluent)'). "
        "Return a JSON array of strings. If none found return []."
    ),
    FieldType.AWARDS: (
        "Extract awards, honours, recognitions, and achievements. "
        "Return a JSON array of strings describing each one. If none found return []."
    ),
    FieldType.VOLUNTEER_EXPERIENCE: (
        "Extract ALL volunteer, community service, or non-profit involvement entries.\n"
    ),
    FieldType.PUBLICATIONS: (
        "Extract ALL publications: journal articles, conference papers, books, "
        "blog posts, or any other published work.\n"
    ),
}


class LLMExtractionStrategy(ExtractionStrategy[List[str]]):
    """Extract using LLM (Gemini). Handles both plain-string and structured-JSON fields.

    For structured fields (work experience, education, etc.) the strategy
    returns a list of JSON-encoded strings — one per entry. The corresponding
    extractor is responsible for deserialising each string into a typed dataclass.
    """

    def __init__(self, spec: FieldSpec, model_name: str = "gemini-2.0-flash"):
        """Initialize with Gemini model.

        Args:
            spec: Field specification
            model_name: Gemini model to use

        Raises:
            InvalidStrategyConfigError: If model init fails or API key missing
        """
        self.spec = spec

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise InvalidStrategyConfigError(
                "GEMINI_API_KEY not found in environment variables. "
                "Please create a .env file with your API key and call load_dotenv() "
                "at your application entry point."
            )

        try:
            genai.configure(api_key=api_key)  # type: ignore
            self.model = genai.GenerativeModel(model_name)  # type: ignore
        except Exception as e:
            raise InvalidStrategyConfigError(
                "Failed to initialize Gemini model", original_exception=e
            ) from e

    def extract(self, text: str) -> List[str]:
        """Extract field using LLM.

        Args:
            text: Resume text to extract from

        Returns:
            For plain fields: list of strings (usually 1 item for scalar fields).
            For structured fields: list of JSON-encoded object strings.

        Raises:
            NoMatchFoundError: If LLM returns nothing useful
            ExternalServiceError: If the API call fails
        """
        if not text or not text.strip():
            raise NoMatchFoundError("Cannot extract from empty text")

        prompt = self._build_prompt(text)

        try:
            response = self.model.generate_content(prompt)  # type: ignore
            if not response or not response.text:
                raise NoMatchFoundError("LLM returned empty response for field")

            return self._parse_response(response.text)

        except NoMatchFoundError:
            raise
        except Exception as e:
            raise ExternalServiceError(
                "Gemini API call failed", original_exception=e
            ) from e

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_prompt(self, text: str, spec: "FieldSpec | None" = None) -> str:
        """Build a field-specific prompt.

        Args:
            text: Resume text to extract from
            spec: Optional FieldSpec override. Defaults to ``self.spec``.
        """
        if spec is None:
            spec = self.spec
        field_type = spec.field_type
        instruction = _FIELD_INSTRUCTIONS.get(field_type)
        if instruction is None:
            raise InvalidStrategyConfigError(
                f"No LLM prompt defined for field type: {field_type.value}"
            )

        is_structured = spec.is_structured or field_type in _STRUCTURED_FIELD_TYPES

        if is_structured:
            schema = _STRUCTURED_SCHEMAS.get(field_type, "{}")
            return (
                f"{instruction}\n"
                f"Return a valid JSON array of objects matching this schema:\n"
                f"{schema}\n"
                f"If nothing is found, return an empty array: []\n\n"
                f"Resume text:\n{text}\n\n"
                f"Response (JSON array only, no markdown):"
            )
        else:
            return (
                f"{instruction}\n\n"
                f"Resume text:\n{text}\n\n"
                f"Response (JSON array only, no markdown):"
            )

    def _parse_response(self, response_text: str) -> List[str]:
        """Parse the raw LLM response into a list of strings.

        For plain fields: each item in the JSON array becomes a string.
        For structured fields: each object in the JSON array is serialised
        back to a compact JSON string so the extractor can deserialise it.
        """
        response_text = response_text.strip()
        field_type = self.spec.field_type
        is_structured = self.spec.is_structured or field_type in _STRUCTURED_FIELD_TYPES

        # Handle NOT_FOUND / empty sentinel before any JSON parsing
        normalised = response_text.strip("'\"`").upper()
        if normalised in {"NOT_FOUND", "NONE", "N/A", "NULL", "UNKNOWN", ""}:
            raise NoMatchFoundError(
                f"LLM could not find field '{field_type.value}'"
            )

        # No JSON array bracket present
        if "[" not in response_text:
            if self.spec.top_k is None and not is_structured:
                # Scalar field — treat plain-text as the single extracted value
                return [response_text]
            raise ExternalServiceError(
                f"LLM response contained no JSON array for '{field_type.value}'"
            )

        # Opening bracket found but closing bracket missing — malformed JSON
        if "]" not in response_text:
            raise ExternalServiceError(
                f"LLM returned malformed JSON (missing ']') for '{field_type.value}'"
            )

        start = response_text.index("[")
        end = response_text.rindex("]") + 1
        json_str = response_text[start:end]

        try:
            parsed = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ExternalServiceError(
                "Failed to parse LLM response as JSON", original_exception=e
            ) from e

        if not isinstance(parsed, list):
            raise ExternalServiceError("LLM response JSON is not an array")

        if not parsed:
            raise NoMatchFoundError(
                f"LLM found no values for field '{field_type.value}'"
            )

        if is_structured:
            # Return each dict as a compact JSON string for the extractor to parse
            return [json.dumps(item, ensure_ascii=False) for item in parsed if item]
        else:
            # Plain strings — coerce each item and apply top_k limit
            results = [str(item).strip() for item in parsed if item]
            if self.spec.top_k is not None and self.spec.top_k > 0:
                results = results[: self.spec.top_k]
            return results
