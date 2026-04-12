import httpx
import pytest

from infrastructure.llm.jobflow_llm import JobflowEmbeddingClient, JobflowLLMClient


@pytest.mark.asyncio
async def test_jobflow_llm_client_batches_extract_fields_in_single_request():
    seen = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.url.path, request.read().decode()))
        return httpx.Response(200, json={"summary": "Summary", "skills": ["Python"]})

    client = JobflowLLMClient(
        base_url="http://jobflow-llm",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )

    result = await client.extract_fields("resume text", ["summary", "skills"])

    assert result["summary"] == "Summary"
    assert seen == [("/extract", '{"text":"resume text","fields":["summary","skills"]}')]


@pytest.mark.asyncio
async def test_embedding_client_returns_float_vector():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"vector": [1, 2.5, 3]})

    client = JobflowEmbeddingClient(
        base_url="http://jobflow-llm",
        model_version="mini",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )

    assert await client.embed("chunk") == [1.0, 2.5, 3.0]
