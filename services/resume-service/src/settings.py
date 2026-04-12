from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Settings:
    grpc_host: str = "0.0.0.0"
    grpc_port: int = 50051
    http_host: str = "0.0.0.0"
    http_port: int = 8080
    database_url: str = "postgresql://postgres:postgres@localhost:5432/jobflow"
    kafka_bootstrap_servers: str = "localhost:9092"
    qdrant_url: str = "http://localhost:6333"
    llm_service_url: str = "http://localhost:8000"
    embedding_model_version: str = "sentence-transformers/all-MiniLM-L6-v2"
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: str | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            grpc_host=os.getenv("GRPC_HOST", "0.0.0.0"),
            grpc_port=int(os.getenv("GRPC_PORT", "50051")),
            http_host=os.getenv("HTTP_HOST", "0.0.0.0"),
            http_port=int(os.getenv("HTTP_PORT", "8080")),
            database_url=os.getenv(
                "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/jobflow"
            ),
            kafka_bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
            qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            llm_service_url=os.getenv("LLM_SERVICE_URL", "http://localhost:8000"),
            embedding_model_version=os.getenv(
                "EMBEDDING_MODEL_VERSION", "sentence-transformers/all-MiniLM-L6-v2"
            ),
            langfuse_public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            langfuse_secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            langfuse_host=os.getenv("LANGFUSE_HOST"),
        )
