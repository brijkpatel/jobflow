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


class LLMExtractionStrategy(ExtractionStrategy[List[str]]):
    """Extract using LLM (best for complex fields like skills)."""

    def __init__(self, spec: FieldSpec, model_name: str = "gemini-2.0-flash-exp"):
        """Initialize with Gemini model.

        Args:
            spec: Field specification
            model_name: Gemini model to use

        Raises:
            InvalidStrategyConfigError: If model init fails
        """
        self.spec = spec

        # Get API key from environment (load_dotenv should be called at app entry point)
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

        Steps:
            1. Build prompt for this field type
            2. Call Gemini API
            3. Parse JSON response
            4. Return results

        Args:
            text: Text to extract from

        Returns:
            List of extracted values

        Raises:
            NoMatchFoundError: If LLM can't find field
            ExternalServiceError: If API fails
        """
        if not text or not text.strip():
            raise NoMatchFoundError("Cannot extract from empty text")

        # Build field-specific prompt
        prompt = self._build_prompt(text, self.spec)

        # Call API
        try:
            response = self.model.generate_content(prompt)  # type: ignore
            if not response or not response.text:
                raise NoMatchFoundError("LLM returned empty response for field")

            result = self._parse_response(response.text, self.spec)
            return result

        except NoMatchFoundError as e:
            raise e
        except Exception as e:
            raise ExternalServiceError(
                "Gemini API call failed", original_exception=e
            ) from e

    def _build_prompt(self, text: str, spec: FieldSpec) -> str:
        """Create prompt based on field type."""
        field_instructions = {
            FieldType.NAME: "Extract the person's full name from the resume text.",
            FieldType.EMAIL: "Extract the person's email address from the resume text.",
            FieldType.SKILLS: "Extract all technical skills mentioned in the resume text as a JSON array.",
        }

        instruction = field_instructions.get(spec.field_type)

        prompt = f"""{instruction}
            Return the result as a valid JSON array of strings.
            If nothing is found, return an empty array: []

            Text:
            {text}
            Response (JSON array only):"""

        return prompt

    def _parse_response(self, response_text: str, spec: FieldSpec) -> List[str]:
        """Parse JSON response from LLM."""
        response_text = response_text.strip()

        if spec.top_k is not None:
            # Expecting JSON array
            try:
                # Extract JSON from response
                if "[" in response_text and "]" in response_text:
                    start = response_text.index("[")
                    end = response_text.rindex("]") + 1
                    json_str = response_text[start:end]
                    result = json.loads(json_str)

                    if not isinstance(result, list):
                        raise ValueError("Response is not a list")

                    # Clean and limit results
                    result = [str(item).strip() for item in result if item]  # type: ignore
                    if spec.top_k > 0:
                        result = result[: spec.top_k]

                    if not result:
                        raise NoMatchFoundError(
                            f"LLM found no values for field '{spec.field_type.value}'"
                        )

                    return result
                else:
                    raise ValueError("No JSON array found in response")

            except (json.JSONDecodeError, ValueError) as e:
                raise ExternalServiceError(
                    "Failed to parse LLM response as JSON", original_exception=e
                ) from e
        else:
            # Single value expected
            if response_text.upper() == "NOT_FOUND" or not response_text:
                raise NoMatchFoundError(
                    f"LLM could not find field '{spec.field_type.value}'"
                )

            return [response_text]
