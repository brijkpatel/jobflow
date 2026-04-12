# jobflow-classifier

Consumes `raw-jobs` from Kafka, enriches with AI classification, embeds, stores in Postgres + Qdrant, and publishes to `classified-jobs`. Also exposes an MCP tool server for `fetch_job_details`.

## Run
```bash
docker compose -f ../../infrastructure/docker/docker-compose.dev.yml up -d
uv sync && uv run python -m src.main
```

## Test
```bash
uv run pytest -m "not integration"
uv run pytest
```

## Structure
- `src/domain/` — Job entity, interfaces (LLMClient, VectorRepository, JobRepository)
- `src/application/` — ClassifyJobUseCase
- `src/infrastructure/kafka/` — Kafka consumer (raw-jobs) + producer (classified-jobs)
- `src/infrastructure/llm/` — JobflowLLMClient (MCP → jobflow-llm)
- `src/infrastructure/qdrant/` — QdrantVectorRepository (job_descriptions collection)
- `src/infrastructure/postgres/` — PostgresJobRepository
- `src/api/mcp/` — MCP tool server: `fetch_job_details(job_id)`

## Protocols
- **Consumes:** Kafka `raw-jobs`
- **Publishes:** Kafka `classified-jobs`
- **Calls:** MCP → `jobflow-llm` (title normalisation, skills, seniority, job_type)
- **Exposes:** MCP tool server `/mcp` — `fetch_job_details(job_id)` used by jobflow-application

## Critical constraint
Embedding model MUST match `resume-service`: `EMBEDDING_MODEL_VERSION=sentence-transformers/all-MiniLM-L6-v2`
Different models = broken Qdrant similarity. Lock via shared env var in Helm values.

## Key rules
- ADK agent pattern — calls jobflow-llm via MCP (not gRPC)
- Owns Postgres `jobs` schema and Qdrant `job_descriptions` collection
- KEDA scales on `raw-jobs` consumer lag (min 0, max 5)
- See `.claude/architecture.md` for Kafka schemas and MCP tool contracts
