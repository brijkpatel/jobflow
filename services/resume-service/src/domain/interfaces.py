"""Domain interfaces (Protocols) for the resume-service.

All interfaces are structural Protocols — no abstract base classes, no
framework imports. Implementations live in the infrastructure layer and are
injected at the composition root (main.py).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional
from typing import runtime_checkable

try:
    from typing import Protocol
except ImportError:  # Python < 3.8
    from typing_extensions import Protocol  # type: ignore

if TYPE_CHECKING:
    from domain.models import ResumeChunk, ResumeData


@runtime_checkable
class IResumeRepository(Protocol):
    """Persistence interface for ResumeData (Postgres)."""

    async def save(self, resume: "ResumeData") -> None:
        """Persist a resume. Sets resume.created_at if not already set."""
        ...

    async def get_by_id(
        self, resume_id: Any, tenant_id: Any
    ) -> Optional["ResumeData"]:
        """Return resume by ID scoped to tenant, or None if not found."""
        ...

    async def get_latest_by_user(
        self, user_id: Any, tenant_id: Any
    ) -> Optional["ResumeData"]:
        """Return the most recently created resume for a user+tenant pair."""
        ...


@runtime_checkable
class IVectorRepository(Protocol):
    """Write-only interface for chunk embeddings (Qdrant).

    Reading vectors is NOT part of GetResume — the read path uses Postgres
    only. Qdrant unavailability must not affect read RPCs.
    """

    async def upsert_chunks(
        self, chunk_embeddings: list[tuple["ResumeChunk", list[float]]]
    ) -> None:
        """Upsert (chunk, vector) pairs into the vector store."""
        ...


@runtime_checkable
class ILLMClient(Protocol):
    """Interface for batched structured field extraction via LLM.

    A single call returns all requested fields to minimise round-trips.
    The implementation is responsible for truncating input to the model's
    context window before calling the backend.
    """

    async def extract_fields(
        self, text: str, fields: list[str]
    ) -> dict[str, Any]:
        """Extract multiple fields from resume text in a single LLM call.

        Args:
            text: Resume plain text (pre-truncated to MAX_LLM_INPUT_CHARS).
            fields: Field names to extract, e.g. ["summary", "work_experience"].

        Returns:
            Dict keyed by field name. Missing or null keys default to None
            (scalars) or [] (list fields) — never raises KeyError on partial
            responses.
        """
        ...


@runtime_checkable
class IEmbeddingClient(Protocol):
    """Interface for batched text embedding.

    One MCP call per resume — all chunks are embedded in a single request.
    """

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts, returning one vector per text.

        Args:
            texts: Non-empty list of strings to embed.

        Returns:
            List of float vectors, one per input text, in the same order.
        """
        ...


@runtime_checkable
class IEventPublisher(Protocol):
    """Interface for publishing domain events to Kafka."""

    async def publish(self, event: dict[str, Any]) -> None:
        """Publish a domain event to the configured topic.

        Args:
            event: Serialisable dict. Must include at minimum 'event' key.
        """
        ...


@runtime_checkable
class IFileParser(Protocol):
    """Interface for parsing raw file bytes into plain text."""

    def parse(self, content: bytes, filename: str) -> str:
        """Parse file content into plain text.

        Args:
            content: Raw file bytes.
            filename: Original filename — used to detect format (pdf, docx…).

        Returns:
            Extracted plain text.

        Raises:
            FileParsingError: If the file cannot be parsed.
            UnsupportedFileFormatError: If the file format is not supported.
        """
        ...


@runtime_checkable
class IFileStorage(Protocol):
    """Interface for fetching files from object storage (OCI)."""

    async def fetch(self, storage_object: str) -> bytes:
        """Fetch a file from object storage by its path.

        Args:
            storage_object: OCI Object Storage path, e.g.
                            "resumes/<tenant_id>/<uuid>.pdf".

        Returns:
            Raw file bytes.

        Raises:
            StorageFetchError: If the object cannot be retrieved.
        """
        ...


@runtime_checkable
class ITracingClient(Protocol):
    """Interface for LLM/embedding call tracing (LangFuse).

    The no-op stub (TracingClientStub) is used until subtask 16 wires the
    real LangFuse client. All call sites use this interface so the swap
    requires no changes outside the composition root.
    """

    def start_trace(self, name: str, metadata: dict[str, Any]) -> Any:
        """Start a trace span. Returns an opaque span handle."""
        ...

    def end_trace(self, span: Any, output: Any) -> None:
        """End a trace span with the given output."""
        ...
