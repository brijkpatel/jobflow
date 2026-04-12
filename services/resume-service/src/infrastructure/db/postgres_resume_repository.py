from __future__ import annotations

import json
import uuid

import asyncpg

from domain.models import ResumeData, ResumeRecord


class PostgresResumeRepository:
    def __init__(self, database_url: str) -> None:
        self._database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
        self._pool: asyncpg.Pool | None = None

    async def save(self, resume: ResumeData, tenant_id: str, user_id: str) -> str:
        pool = await self._pool_or_connect()
        resume_id = str(uuid.uuid4())
        await pool.execute(
            """
            INSERT INTO resumes (resume_id, tenant_id, user_id, resume_payload)
            VALUES ($1, $2, $3, $4::jsonb)
            """,
            resume_id,
            tenant_id,
            user_id,
            json.dumps(resume.to_dict()),
        )
        return resume_id

    async def get(self, resume_id: str, tenant_id: str) -> ResumeRecord | None:
        pool = await self._pool_or_connect()
        row = await pool.fetchrow(
            """
            SELECT resume_id, tenant_id, user_id, resume_payload
            FROM resumes
            WHERE resume_id = $1 AND tenant_id = $2
            """,
            resume_id,
            tenant_id,
        )
        return self._record_from_row(row)

    async def get_latest_for_user(self, tenant_id: str, user_id: str) -> ResumeRecord | None:
        pool = await self._pool_or_connect()
        row = await pool.fetchrow(
            """
            SELECT resume_id, tenant_id, user_id, resume_payload
            FROM resumes
            WHERE tenant_id = $1 AND user_id = $2
            ORDER BY created_at DESC
            LIMIT 1
            """,
            tenant_id,
            user_id,
        )
        return self._record_from_row(row)

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()

    async def _pool_or_connect(self) -> asyncpg.Pool:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(self._database_url)
            await self._pool.execute(
                """
                CREATE TABLE IF NOT EXISTS resumes (
                    resume_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    resume_payload JSONB NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        return self._pool

    def _record_from_row(self, row: asyncpg.Record | None) -> ResumeRecord | None:
        if row is None:
            return None
        return ResumeRecord(
            resume_id=row["resume_id"],
            tenant_id=row["tenant_id"],
            user_id=row["user_id"],
            resume=ResumeData.from_dict(dict(row["resume_payload"])),
        )
