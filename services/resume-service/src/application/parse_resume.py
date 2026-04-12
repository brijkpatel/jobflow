from __future__ import annotations

from datetime import UTC, datetime

from domain.exceptions import UnsupportedFileFormatError
from domain.interfaces import EmbeddingClient, EventPublisher, FileParser, ResumeRepository, VectorRepository
from domain.models import ParseResumeResult

from .chunking import build_resume_chunks, calculate_years_of_experience
from .extraction import ResumeExtractionOrchestrator


class ParseResumeUseCase:
    def __init__(
        self,
        *,
        parsers: dict[str, FileParser],
        extractor: ResumeExtractionOrchestrator,
        embedding_client: EmbeddingClient,
        resume_repository: ResumeRepository,
        vector_repository: VectorRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._parsers = parsers
        self._extractor = extractor
        self._embedding_client = embedding_client
        self._resume_repository = resume_repository
        self._vector_repository = vector_repository
        self._event_publisher = event_publisher

    async def execute(
        self, *, file_bytes: bytes, filename: str, tenant_id: str, user_id: str
    ) -> ParseResumeResult:
        parser = self._parsers.get(_extension(filename))
        if parser is None:
            raise UnsupportedFileFormatError(f"Unsupported file format for {filename}")
        text = parser.parse(file_bytes, filename)
        resume = await self._extractor.extract(text)
        resume.years_of_experience = calculate_years_of_experience(resume)
        chunks = build_resume_chunks(resume)
        for index, chunk in enumerate(chunks):
            chunk.chunk_index = index
            chunk.embedding = await self._embedding_client.embed(chunk.text)
        resume_id = await self._resume_repository.save(
            resume=resume, tenant_id=tenant_id, user_id=user_id
        )
        await self._vector_repository.upsert_chunks(
            resume_id=resume_id, user_id=user_id, tenant_id=tenant_id, chunks=chunks
        )
        await self._event_publisher.publish_resume_parsed(
            resume_id=resume_id,
            tenant_id=tenant_id,
            user_id=user_id,
            chunk_count=len(chunks),
            parsed_at=datetime.now(tz=UTC).isoformat(),
        )
        return ParseResumeResult(resume_id=resume_id, resume=resume, chunks=chunks)

    async def get_resume(self, *, resume_id: str, tenant_id: str):
        return await self._resume_repository.get(resume_id=resume_id, tenant_id=tenant_id)


def _extension(filename: str) -> str:
    return "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
