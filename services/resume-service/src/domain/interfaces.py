from __future__ import annotations

from typing import Any, Generic, Protocol, TypeVar

from .models import ResumeChunk, ResumeData, ResumeRecord

T = TypeVar("T")


class FileParser(Protocol):
    def parse(self, file_bytes: bytes, filename: str) -> str:
        """Parse bytes into raw text."""


class ExtractionStrategy(Protocol, Generic[T]):
    def extract(self, text: str) -> T:
        """Extract a structured value from text."""


class ResumeRepository(Protocol):
    async def save(self, resume: ResumeData, tenant_id: str, user_id: str) -> str:
        """Persist a resume and return its id."""

    async def get(self, resume_id: str, tenant_id: str) -> ResumeRecord | None:
        """Fetch a persisted resume by id."""

    async def get_latest_for_user(
        self, tenant_id: str, user_id: str
    ) -> ResumeRecord | None:
        """Fetch the latest resume for a user."""


class LLMClient(Protocol):
    async def extract_fields(self, text: str, fields: list[str]) -> dict[str, Any]:
        """Extract multiple fields in a single batched call."""


class EmbeddingClient(Protocol):
    async def embed(self, text: str) -> list[float]:
        """Embed a text chunk."""


class VectorRepository(Protocol):
    async def upsert_chunks(
        self, resume_id: str, user_id: str, tenant_id: str, chunks: list[ResumeChunk]
    ) -> None:
        """Persist embedded chunks to vector storage."""


class EventPublisher(Protocol):
    async def publish_resume_parsed(
        self,
        *,
        resume_id: str,
        tenant_id: str,
        user_id: str,
        chunk_count: int,
        parsed_at: str,
    ) -> None:
        """Publish a resume-parsed event."""
