from __future__ import annotations

from qdrant_client import AsyncQdrantClient, models

from domain.models import ResumeChunk


class QdrantVectorRepository:
    def __init__(self, *, url: str, collection_name: str = "resume_chunks") -> None:
        self._client = AsyncQdrantClient(url=url)
        self._collection_name = collection_name

    async def upsert_chunks(
        self, resume_id: str, user_id: str, tenant_id: str, chunks: list[ResumeChunk]
    ) -> None:
        if not chunks:
            return
        vector_size = len(chunks[0].embedding or [])
        if vector_size == 0:
            raise ValueError("chunks must be embedded before upsert")
        await self._ensure_collection(vector_size)
        points = [
            models.PointStruct(
                id=f"{resume_id}:{chunk.chunk_index}",
                vector=chunk.embedding or [],
                payload={
                    "resume_id": resume_id,
                    "user_id": user_id,
                    "tenant_id": tenant_id,
                    "section_type": chunk.section_type,
                    "text": chunk.text,
                    "chunk_index": chunk.chunk_index,
                },
            )
            for chunk in chunks
        ]
        await self._client.upsert(collection_name=self._collection_name, points=points)

    async def _ensure_collection(self, vector_size: int) -> None:
        collections = await self._client.get_collections()
        names = {item.name for item in collections.collections}
        if self._collection_name not in names:
            await self._client.create_collection(
                collection_name=self._collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE,
                ),
            )
