from __future__ import annotations

from domain.interfaces import ResumeRepository


class FetchUserResumeTool:
    name = "fetch_user_resume"
    description = "Fetch the latest parsed resume for a tenant-scoped user."
    input_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["tenant_id", "user_id"],
        "properties": {
            "tenant_id": {"type": "string", "minLength": 1},
            "user_id": {"type": "string", "minLength": 1},
        },
    }

    def __init__(self, repository: ResumeRepository) -> None:
        self._repository = repository

    async def handle(self, tenant_id: str, user_id: str) -> dict:
        record = await self._repository.get_latest_for_user(tenant_id=tenant_id, user_id=user_id)
        if record is None:
            raise LookupError(f"no resume found for user {user_id}")
        return {"resume_id": record.resume_id, "resume": record.resume.to_dict()}
