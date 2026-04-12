from __future__ import annotations

import json

from aiokafka import AIOKafkaProducer


class ResumeEventPublisher:
    def __init__(
        self,
        *,
        bootstrap_servers: str,
        topic: str = "resume-parsed",
    ) -> None:
        self._producer = AIOKafkaProducer(bootstrap_servers=bootstrap_servers)
        self._started = False
        self._topic = topic

    async def publish_resume_parsed(
        self,
        *,
        resume_id: str,
        tenant_id: str,
        user_id: str,
        chunk_count: int,
        parsed_at: str,
    ) -> None:
        if not self._started:
            await self._producer.start()
            self._started = True
        payload = json.dumps(
            {
                "resume_id": resume_id,
                "tenant_id": tenant_id,
                "user_id": user_id,
                "chunk_count": chunk_count,
                "parsed_at": parsed_at,
            }
        ).encode("utf-8")
        await self._producer.send_and_wait(self._topic, payload)

    async def close(self) -> None:
        if self._started:
            await self._producer.stop()
