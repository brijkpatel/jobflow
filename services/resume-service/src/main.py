from __future__ import annotations

import asyncio
from contextlib import suppress

import grpc
import httpx

from api.grpc import ResumeServiceHandler, add_resume_service_to_server
from api.health import HealthServer
from application import ParseResumeUseCase, ResumeExtractionOrchestrator
from infrastructure import (
    FetchUserResumeTool,
    GLiNERExtractionStrategy,
    JobflowEmbeddingClient,
    JobflowLLMClient,
    PDFParser,
    PostgresResumeRepository,
    QdrantVectorRepository,
    RegexExtractionStrategy,
    ResumeEventPublisher,
    WordParser,
)
from settings import Settings


def build_application(settings: Settings):
    http_client = httpx.AsyncClient(timeout=30.0)
    llm_client = JobflowLLMClient(base_url=settings.llm_service_url, http_client=http_client)
    embedding_client = JobflowEmbeddingClient(
        base_url=settings.llm_service_url,
        model_version=settings.embedding_model_version,
        http_client=http_client,
    )
    repository = PostgresResumeRepository(settings.database_url)
    vector_repository = QdrantVectorRepository(url=settings.qdrant_url)
    publisher = ResumeEventPublisher(bootstrap_servers=settings.kafka_bootstrap_servers)
    extractor = ResumeExtractionOrchestrator(
        llm_client=llm_client,
        simple_field_strategies={
            "name": [GLiNERExtractionStrategy(label="person")],
            "email": [RegexExtractionStrategy(r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})")],
            "phone": [RegexExtractionStrategy(r"(\+?\d[\d\-\s()]{7,}\d)")],
            "linkedin_url": [RegexExtractionStrategy(r"(https?://(?:www\.)?linkedin\.com/[^\s]+)")],
            "github_url": [RegexExtractionStrategy(r"(https?://(?:www\.)?github\.com/[^\s]+)")],
            "portfolio_url": [
                RegexExtractionStrategy(
                    r"(https?://(?!(?:www\.)?(?:linkedin|github)\.com)[^\s]+)"
                )
            ],
            "location": [GLiNERExtractionStrategy(label="location")],
        },
    )
    use_case = ParseResumeUseCase(
        parsers={".pdf": PDFParser(), ".docx": WordParser(), ".doc": WordParser()},
        extractor=extractor,
        embedding_client=embedding_client,
        resume_repository=repository,
        vector_repository=vector_repository,
        event_publisher=publisher,
    )
    mcp_tool = FetchUserResumeTool(repository)
    return {
        "http_client": http_client,
        "health_server": HealthServer(
            settings.http_host,
            settings.http_port,
            mcp_tool=mcp_tool,
        ),
        "mcp_tool": mcp_tool,
        "publisher": publisher,
        "repository": repository,
        "service_handler": ResumeServiceHandler(use_case),
        "use_case": use_case,
    }


async def serve(settings: Settings) -> None:
    app = build_application(settings)
    app["health_server"].start()
    server = grpc.aio.server()
    add_resume_service_to_server(server, app["service_handler"])
    server.add_insecure_port(f"{settings.grpc_host}:{settings.grpc_port}")
    await server.start()
    try:
        await server.wait_for_termination()
    finally:
        await server.stop(grace=None)
        await app["publisher"].close()
        await app["repository"].close()
        await app["http_client"].aclose()
        app["health_server"].stop()


def main() -> None:
    settings = Settings.from_env()
    with suppress(KeyboardInterrupt):
        asyncio.run(serve(settings))


if __name__ == "__main__":
    main()
