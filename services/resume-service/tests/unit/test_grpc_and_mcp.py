from types import SimpleNamespace

import pytest

from api.grpc.service import ResumeServiceHandler, _resume_to_proto
from api.health import _handle_jsonrpc
from domain.models import Certification, Education, Experience, Project, ResumeData, ResumeRecord
from infrastructure.mcp.server import FetchUserResumeTool


class FakeUseCase:
    async def execute(self, **kwargs):
        return SimpleNamespace(resume_id="resume-123", resume=ResumeData(name="Ada", skills=["Python"]))

    async def get_resume(self, *, resume_id: str, tenant_id: str):
        return ResumeRecord(
            resume_id=resume_id,
            tenant_id=tenant_id,
            user_id="user-1",
            resume=ResumeData(name="Ada"),
        )


class MissingUseCase(FakeUseCase):
    async def get_resume(self, *, resume_id: str, tenant_id: str):
        return None


class AbortContext:
    def __init__(self) -> None:
        self.message = None

    async def abort(self, code, message):
        self.message = message
        raise RuntimeError(message)


class FakeRepository:
    async def get_latest_for_user(self, tenant_id: str, user_id: str):
        return ResumeRecord(
            resume_id="resume-123",
            tenant_id=tenant_id,
            user_id=user_id,
            resume=ResumeData(name="Ada"),
        )


@pytest.mark.asyncio
async def test_grpc_handler_returns_proto_payload_when_generated_stubs_exist():
    handler = ResumeServiceHandler(FakeUseCase())

    response = await handler.ParseResume(
        SimpleNamespace(file_bytes=b"bytes", filename="resume.pdf", tenant_id="tenant", user_id="user"),
        AbortContext(),
    )

    assert response.resume_id == "resume-123"
    assert response.resume.name == "Ada"


@pytest.mark.asyncio
async def test_grpc_handler_aborts_when_resume_is_missing():
    handler = ResumeServiceHandler(MissingUseCase())

    with pytest.raises(RuntimeError, match="resume missing not found"):
        await handler.GetResume(
            SimpleNamespace(resume_id="missing", tenant_id="tenant"),
            AbortContext(),
        )


@pytest.mark.asyncio
async def test_fetch_user_resume_tool_returns_latest_resume():
    tool = FetchUserResumeTool(FakeRepository())

    result = await tool.handle(tenant_id="tenant", user_id="user")

    assert result["resume_id"] == "resume-123"
    assert result["resume"]["name"] == "Ada"


def test_proto_conversion_preserves_absent_optional_fields():
    proto = _resume_to_proto(ResumeData())

    assert not proto.HasField("name")
    assert not proto.HasField("years_of_experience")


def test_nested_proto_conversion_preserves_absent_optional_fields():
    proto = _resume_to_proto(
        ResumeData(
            experience=[Experience(company="Jobflow", title="Engineer", start_date="2024-01")],
            education=[Education(institution="State U", degree="BS")],
            certifications=[Certification(name="AWS SA")],
            projects=[Project(name="Resume Parser")],
        )
    )

    assert not proto.experience[0].HasField("end_date")
    assert not proto.experience[0].HasField("location")
    assert not proto.education[0].HasField("field")
    assert not proto.education[0].HasField("graduation_date")
    assert not proto.education[0].HasField("gpa")
    assert not proto.certifications[0].HasField("issuer")
    assert not proto.certifications[0].HasField("date")
    assert not proto.projects[0].HasField("description")


def test_mcp_jsonrpc_returns_error_payload_for_tool_failures():
    class MissingRepository:
        async def get_latest_for_user(self, tenant_id: str, user_id: str):
            return None

    tool = FetchUserResumeTool(MissingRepository())

    response = _handle_jsonrpc(
        tool,
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool.name, "arguments": {"tenant_id": "tenant", "user_id": "user"}},
        },
    )

    assert response["error"]["code"] == -32000
    assert "no resume found" in response["error"]["message"]
