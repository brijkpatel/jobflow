import pytest

from application.parse_resume import ParseResumeUseCase
from domain.models import ResumeData


class FakeParser:
    def parse(self, file_bytes: bytes, filename: str) -> str:
        assert filename == "resume.pdf"
        return "parsed text"


class FakeExtractor:
    async def extract(self, text: str) -> ResumeData:
        assert text == "parsed text"
        return ResumeData(summary="Summary", skills=["Python"])


class FakeEmbeddingClient:
    def __init__(self) -> None:
        self.calls = []

    async def embed(self, text: str) -> list[float]:
        self.calls.append(text)
        return [0.1, 0.2, 0.3]


class FakeRepository:
    def __init__(self) -> None:
        self.saved = None

    async def save(self, resume: ResumeData, tenant_id: str, user_id: str) -> str:
        self.saved = (resume, tenant_id, user_id)
        return "resume-123"

    async def get(self, resume_id: str, tenant_id: str):
        raise AssertionError("not used")


class FakeVectorRepository:
    def __init__(self) -> None:
        self.upserts = []

    async def upsert_chunks(self, resume_id: str, user_id: str, tenant_id: str, chunks):
        self.upserts.append((resume_id, user_id, tenant_id, chunks))


class FakePublisher:
    def __init__(self) -> None:
        self.events = []

    async def publish_resume_parsed(self, **payload):
        self.events.append(payload)


@pytest.mark.asyncio
async def test_parse_use_case_orchestrates_parse_extract_embed_store_and_publish():
    embedding = FakeEmbeddingClient()
    repository = FakeRepository()
    vector_repository = FakeVectorRepository()
    publisher = FakePublisher()
    use_case = ParseResumeUseCase(
        parsers={".pdf": FakeParser()},
        extractor=FakeExtractor(),
        embedding_client=embedding,
        resume_repository=repository,
        vector_repository=vector_repository,
        event_publisher=publisher,
    )

    result = await use_case.execute(
        file_bytes=b"pdf-bytes",
        filename="resume.pdf",
        tenant_id="tenant-1",
        user_id="user-1",
    )

    assert result.resume_id == "resume-123"
    assert repository.saved[1:] == ("tenant-1", "user-1")
    assert embedding.calls == ["Summary", "Python"]
    assert vector_repository.upserts[0][0:3] == ("resume-123", "user-1", "tenant-1")
    assert publisher.events[0]["chunk_count"] == 2
