from __future__ import annotations

from threading import Lock


class GLiNERExtractionStrategy:
    _model = None
    _lock = Lock()

    def __init__(self, *, label: str, model_name: str = "urchade/gliner_multi_pii-v1") -> None:
        self._label = label
        self._model_name = model_name

    def extract(self, text: str) -> list[str]:
        model = self._load_model()
        entities = model.predict_entities(text, [self._label])
        return [entity["text"].strip() for entity in entities if entity.get("text")]

    def _load_model(self):
        if self.__class__._model is None:
            with self.__class__._lock:
                if self.__class__._model is None:
                    from gliner import GLiNER  # type: ignore

                    self.__class__._model = GLiNER.from_pretrained(self._model_name)
        return self.__class__._model
