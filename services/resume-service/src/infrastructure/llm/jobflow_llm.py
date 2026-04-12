from __future__ import annotations

from contextlib import nullcontext
from typing import Any, Callable, ContextManager

import httpx


TraceFactory = Callable[[str, dict[str, Any]], ContextManager[object]]


class JobflowLLMClient:
    def __init__(
        self,
        *,
        base_url: str,
        http_client: httpx.AsyncClient | None = None,
        trace_factory: TraceFactory | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._http_client = http_client or httpx.AsyncClient(timeout=30.0)
        self._trace_factory = trace_factory

    async def extract_fields(self, text: str, fields: list[str]) -> dict[str, Any]:
        payload = {"text": text, "fields": fields}
        with self._trace("jobflow-llm.extract", {"field_count": len(fields)}):
            response = await self._http_client.post(f"{self._base_url}/extract", json=payload)
        response.raise_for_status()
        body = response.json()
        if not isinstance(body, dict):
            raise ValueError("jobflow-llm /extract returned a non-object payload")
        return body

    def _trace(self, name: str, metadata: dict[str, Any]):
        if self._trace_factory is None:
            return nullcontext()
        return self._trace_factory(name, metadata)


class JobflowEmbeddingClient:
    def __init__(
        self,
        *,
        base_url: str,
        model_version: str,
        http_client: httpx.AsyncClient | None = None,
        trace_factory: TraceFactory | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model_version = model_version
        self._http_client = http_client or httpx.AsyncClient(timeout=30.0)
        self._trace_factory = trace_factory

    async def embed(self, text: str) -> list[float]:
        payload = {"text": text, "model": self._model_version}
        with self._trace("jobflow-llm.embed", {"model": self._model_version}):
            response = await self._http_client.post(f"{self._base_url}/embed", json=payload)
        response.raise_for_status()
        body = response.json()
        vector = body.get("vector")
        if not isinstance(vector, list) or not all(isinstance(item, (int, float)) for item in vector):
            raise ValueError("jobflow-llm /embed returned an invalid vector payload")
        return [float(item) for item in vector]

    def _trace(self, name: str, metadata: dict[str, Any]):
        if self._trace_factory is None:
            return nullcontext()
        return self._trace_factory(name, metadata)
