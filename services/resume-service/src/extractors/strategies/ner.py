"""Extract fields using Named Entity Recognition (transformers)."""

from typing import List, Optional
from gliner import GLiNER  # type: ignore

from interfaces import ExtractionStrategy, FieldSpec
from exceptions import (
    InvalidStrategyConfigError,
    NoMatchFoundError,
    StrategyExtractionError,
)


class NERExtractionStrategy(ExtractionStrategy[List[str]]):
    """Extract using NER models (good for names, skills)."""

    def __init__(
        self,
        spec: FieldSpec,
        model_name: str = "urchade/gliner_multi_pii-v1",
        default_entity_label: Optional[str] = None,
    ):
        """Initialize NER with GLiNER model (~500MB download on first run).

        Args:
            spec: Field specification
            model_name: GLiNER model to use
            default_entity_label: Fallback if spec doesn't have entity_label

        Raises:
            InvalidStrategyConfigError: If model load fails
        """
        self.spec = spec
        self.default_entity_label = default_entity_label
        try:
            self.model = GLiNER.from_pretrained(model_name)  # type: ignore
        except Exception as e:
            raise InvalidStrategyConfigError(
                "Failed to load GLiNER model", original_exception=e
            ) from e

    def extract(self, text: str) -> List[str]:
        """Extract entities using NER.

        Steps:
            1. Get entity label to search for
            2. Run GLiNER model on text
            3. Extract entity texts
            4. Return top_k results

        Args:
            text: Text to extract from

        Returns:
            List of entity texts

        Raises:
            NoMatchFoundError: If no entities found
        """
        if not text or not text.strip():
            raise NoMatchFoundError("Cannot extract from empty text")

        # Determine what entity type to look for
        entity_labels = None
        if self.spec.entity_label:
            entity_labels = [self.spec.entity_label]
        elif self.default_entity_label:
            entity_labels = [self.default_entity_label]

        if not entity_labels:
            raise InvalidStrategyConfigError(
                "entity_label must be provided in FieldSpec or as default_entity_label"
            )

        # Run NER model
        try:
            entities = self.model.predict_entities(text, entity_labels)  # type: ignore
        except Exception as e:
            raise StrategyExtractionError(
                "GLiNER processing failed", original_exception=e
            ) from e

        # Extract text from results
        entity_texts: List[str] = [ent["text"] for ent in entities]  # type: ignore

        if not entity_texts:
            raise NoMatchFoundError("No entities found")

        # Return with limit if specified
        if self.spec.top_k is not None:
            return (
                entity_texts[: self.spec.top_k] if self.spec.top_k > 0 else entity_texts
            )
        else:
            return [entity_texts[0]]
