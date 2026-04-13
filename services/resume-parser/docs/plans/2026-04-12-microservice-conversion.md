---
task: microservice-conversion
reviewers: developer, qa, compliance, regression, architect, ml-developer
branch: task/resume-service/microservice-conversion
---

## Problem

`services/resume-parser` was built as a standalone interview challenge. It calls Gemini directly
(hard-coded API key), has no service layers, no gRPC/Kafka/MCP contracts, and cannot be deployed
as a jobflow microservice. It must be restructured into the hexagonal architecture defined in
`.claude/coding-standards.md`, wired to jobflow contracts, and integrated with `jobflow-llm`
instead of Gemini.

## Solution approach

Restructure the service in place, following the domain/application/infrastructure/api layering
mandated by coding-standards.md. Keep the working extraction logic (regex, NER, chain-of-fallback)
— it is the only part worth preserving. Replace the Gemini-specific `LLMExtractionStrategy` with
an `ILLMClient` Protocol so the backend can be swapped via config. Consolidate the 5 LLM-extracted
structured fields into a single batched call (summary, work_experience, education, certifications,
projects) instead of one call per field — this cuts LLM round trips from 5× to 1×.

**Rejected alternatives:**
- _Keep Gemini as a secondary adapter_: unnecessary complexity; no in-project use case for Gemini.
- _Build a new extraction layer from scratch_: the existing regex/NER extractors are correct and
  well-tested; reuse them, keep `ResumeExtractor` as the orchestrator.
- _FastAPI instead of gRPC_: architecture doc mandates gRPC for jobflow-api → resume-service
  (sync, internal, user waits).

**Key design decisions:**
- `ILLMClient` Protocol lives in `domain/interfaces.py`; `JobflowLLMClient` (calls `jobflow-llm`
  MCP server) and `GeminiLLMClient` (kept for local dev only) live in `infrastructure/llm/`.
  Active backend selected by `LLM_BACKEND` env var (`jobflow-llm` | `gemini`).
- Batched extraction: `ILLMClient.extract_fields(text, fields) → dict` — one HTTP/MCP call returns
  all 5 structured fields; `LLMExtractionStrategy` is replaced by `BatchedLLMExtractor`.
- `ResumeData` gains `resume_id: UUID`, `user_id: UUID`, `created_at: datetime` — required
  identifiers for persistence and gRPC response. Remove `to_dict()` / `to_json()` serialization
  helpers (serialization is infrastructure concern).
- `ResumeChunk` is a new domain value object: `{chunk_id, resume_id, user_id, section, text,
  embedding: list[float]}` — one chunk per logical section (summary, each work entry, skills).
- `ParseResumeUseCase` orchestrates: parse text → regex/NER extract → batched LLM extract →
  assemble `ResumeData` → chunk → embed → save to Postgres → upsert to Qdrant → publish
  `resume-parsed` Kafka event.
- Rename `services/resume-parser` → `services/resume-service` as part of restructuring.

## Interfaces & contracts

| Artifact | Change | File |
|---|---|---|
| `ResumeService.ParseResume` gRPC | create | `contracts/proto/resume.proto` |
| `ResumeService.GetResume` gRPC | create | `contracts/proto/resume.proto` |
| `resume-parsed` Kafka topic | create | `contracts/kafka/schemas/resume-parsed.json` |
| `fetch_user_resume` MCP tool | create | `contracts/mcp/tools/fetch-user-resume.json` |
| `resume_service` SQL schema | create | `contracts/migrations/003_resume_service.sql` |
| `impact-map.json` | add `resume-parsed` + `fetch-user-resume` consumers | `contracts/impact-map.json` |

### Proto shape

```proto
service ResumeService {
  rpc ParseResume(ParseResumeRequest) returns (ParseResumeResponse);
  rpc GetResume(GetResumeRequest)     returns (GetResumeResponse);
}

message ParseResumeRequest {
  string user_id   = 1;  // UUID
  bytes  file_data = 2;
  string file_name = 3;  // "resume.pdf" | "resume.docx"
}

message ParseResumeResponse {
  string resume_id   = 1;
  string user_id     = 2;
  ResumeProto resume = 3;
}

message GetResumeRequest  { string user_id = 1; }
message GetResumeResponse { string resume_id = 1; ResumeProto resume = 2; }
```

`ResumeProto` mirrors `ResumeData` domain model (all fields, nested messages for structured
sections). Full field list matches existing model; `enriched_skills` omitted for MVP
(compute-heavy, deferred to classifier).

### Kafka — `resume-parsed` schema

```json
{
  "event": "resume-parsed",
  "resume_id": "<uuid>",
  "user_id": "<uuid>",
  "created_at": "<iso8601>"
}
```

Producer: `resume-service`. No consumers at contract-definition time; consumers added as
`jobflow-matcher` and `jobflow-application` are built.

### MCP — `fetch_user_resume`

Input: `{ "user_id": "<uuid>" }`. Returns full `ResumeProto`-equivalent JSON.
Consumed by: `jobflow-application` ADK agents.

### SQL — `contracts/migrations/003_resume_service.sql`

Tables: `resumes` (resume_id PK, user_id, name, email, raw_text, parsed_at, created_at) +
`resume_sections` (section_id PK, resume_id FK, section_type, content, created_at).
Qdrant collection schema defined in code (not SQL).

## Files to change

### Deleted (standalone artifacts, not needed in service)
| File | Action |
|---|---|
| `services/resume-parser/examples.py` | delete |
| `services/resume-parser/README.md` | delete |
| `services/resume-parser/TESTING.md` | delete |
| `services/resume-parser/sample_resumes/` | delete |
| `services/resume-parser/src/parsers/tests/generate_test_pdfs.py` | delete |
| `services/resume-parser/src/parsers/tests/generate_test_data.py` | delete |

### New contract files
| File | Action |
|---|---|
| `contracts/proto/resume.proto` | create |
| `contracts/kafka/schemas/resume-parsed.json` | create |
| `contracts/mcp/tools/fetch-user-resume.json` | create |
| `contracts/migrations/003_resume_service.sql` | create |
| `contracts/impact-map.json` | modify |

### Service — rename + restructure (services/resume-parser → services/resume-service)
| File | Action | What changes |
|---|---|---|
| `services/resume-service/src/domain/models.py` | create | Consolidates existing `models/` dataclasses; adds `resume_id`, `user_id`, `created_at` to `ResumeData`; adds `ResumeChunk`; removes `to_dict`/`to_json` |
| `services/resume-service/src/domain/interfaces.py` | create | `IResumeRepository`, `IVectorRepository`, `ILLMClient`, `IEventPublisher`, `IFileParser` Protocols |
| `services/resume-service/src/domain/exceptions.py` | create | Consolidates existing `exceptions/` |
| `services/resume-service/src/application/use_cases.py` | create | `ParseResumeUseCase` — orchestrates parse → extract → embed → save → publish |
| `services/resume-service/src/infrastructure/llm/jobflow_client.py` | create | `JobflowLLMClient(ILLMClient)` — calls `jobflow-llm` MCP `/extract` endpoint; batched |
| `services/resume-service/src/infrastructure/llm/gemini_client.py` | create | `GeminiLLMClient(ILLMClient)` — local dev fallback; wraps existing `LLMExtractionStrategy` |
| `services/resume-service/src/infrastructure/llm/config.py` | create | `build_llm_client(settings) → ILLMClient` factory; reads `LLM_BACKEND` |
| `services/resume-service/src/infrastructure/postgres/repository.py` | create | `PostgresResumeRepository(IResumeRepository)` — asyncpg; save + get by user_id |
| `services/resume-service/src/infrastructure/qdrant/repository.py` | create | `QdrantVectorRepository(IVectorRepository)` — upsert/query `resume_chunks` collection |
| `services/resume-service/src/infrastructure/kafka/publisher.py` | create | `KafkaEventPublisher(IEventPublisher)` — aiokafka; publishes `resume-parsed` |
| `services/resume-service/src/infrastructure/parsers/pdf.py` | create | Move + rename `src/parsers/pdf_parser.py` |
| `services/resume-service/src/infrastructure/parsers/word.py` | create | Move + rename `src/parsers/word_parser.py` |
| `services/resume-service/src/infrastructure/extractors/` | create | Move existing `extractors/` tree; replace `LLMExtractionStrategy` with `BatchedLLMExtractor` that delegates to `ILLMClient` |
| `services/resume-service/src/api/grpc/server.py` | create | gRPC servicer; calls `ParseResumeUseCase`; maps domain ↔ proto |
| `services/resume-service/src/api/grpc/generated/` | create | Output of `python -m grpc_tools.protoc` on `resume.proto` |
| `services/resume-service/src/api/mcp/tools.py` | create | FastMCP server exposing `fetch_user_resume` tool |
| `services/resume-service/src/config.py` | create | Pydantic `Settings` — reads all env vars; single source of truth |
| `services/resume-service/src/main.py` | create | Composition root — wires all adapters; starts gRPC + MCP servers |
| `services/resume-service/pyproject.toml` | create (replaces old) | Rename to `resume-service`; drop `google-generativeai` from required deps (move to `extras`); add `grpcio`, `grpcio-tools`, `asyncpg`, `qdrant-client`, `aiokafka`, `fastmcp`, `sentence-transformers`, `pydantic-settings`, `langfuse` |
| `services/resume-service/Dockerfile` | create | Multi-stage, `--platform linux/arm64`; pre-bakes GLiNER weights at build time |
| `services/resume-service/.env.example` | create | All required env vars with placeholder values |

### Tests
| File | Action | What changes |
|---|---|---|
| `services/resume-service/tests/unit/test_use_cases.py` | create | Unit tests for `ParseResumeUseCase` with mocked adapters |
| `services/resume-service/tests/unit/test_batched_extractor.py` | create | Unit tests for `BatchedLLMExtractor` with mocked `ILLMClient` |
| `services/resume-service/tests/unit/test_domain_models.py` | create | Replace `models/tests/test_resume_data.py`; covers new fields |
| `services/resume-service/tests/unit/test_parsers.py` | create | Merge existing pdf + word parser tests |
| `services/resume-service/tests/unit/test_extractors.py` | create | Merge existing extractor tests (non-LLM strategies only) |
| `services/resume-service/tests/integration/test_grpc_server.py` | create | gRPC round-trip with mocked use case |
| `services/resume-service/tests/integration/test_postgres_repository.py` | create | Real asyncpg against Docker Postgres |
| `services/resume-service/tests/integration/test_qdrant_repository.py` | create | Real Qdrant client against Docker Qdrant |

## Test strategy

- **Unit** — `ParseResumeUseCase` calls adapters in correct order (mock all 4 interfaces)
  - `test_parse_resume_happy_path()` — PDF bytes in, `ResumeData` with `resume_id` out, all adapters called once
  - `test_parse_resume_llm_failure_returns_partial_data()` — `ILLMClient` raises; structured fields are `None`; non-LLM fields still populated
  - `test_parse_resume_postgres_failure_raises_domain_exception()` — repository raises; use case propagates
- **Unit** — `BatchedLLMExtractor`
  - `test_batched_extract_returns_all_5_fields()` — mock client returns JSON with all 5 keys
  - `test_batched_extract_partial_response_fills_none()` — mock returns only 3 keys; missing fields are `None`
  - `test_batched_extract_malformed_json_raises_extraction_error()` — mock returns invalid JSON
- **Unit** — `LLM_BACKEND` config factory
  - `test_build_llm_client_defaults_to_jobflow()` — env unset → `JobflowLLMClient`
  - `test_build_llm_client_gemini_selected_by_env()` — `LLM_BACKEND=gemini` → `GeminiLLMClient`
- **Unit** — domain model `ResumeData`
  - `test_resume_data_requires_resume_id()` — omit field → `TypeError`
  - `test_resume_chunk_section_types()` — valid section enum values
- **Unit** — existing extractor tests (path updated, logic unchanged)
  - All tests in `extractors/tests/` move to `tests/unit/test_extractors.py`
- **Integration** — `PostgresResumeRepository`
  - `test_save_and_get_resume_round_trip()` — save then fetch same `resume_id`
  - `test_get_resume_not_found_returns_none()` — unknown `user_id`
- **Integration** — `QdrantVectorRepository`
  - `test_upsert_and_query_chunks()` — upsert 3 chunks, query by vector, all returned
- **Integration** — gRPC server
  - `test_parse_resume_grpc_returns_populated_response()` — real gRPC call, mocked use case

## Acceptance criteria

- [ ] `ParseResume` gRPC call with a real PDF returns populated `ParseResumeResponse` with all
      non-empty fields (name, email, skills, at least one work entry)
- [ ] `GetResume` returns previously saved resume for the same `user_id`
- [ ] `fetch_user_resume` MCP tool returns identical data as `GetResume` for the same `user_id`
- [ ] `resume-parsed` Kafka event is published after successful parse (verified in integration test)
- [ ] `LLM_BACKEND=gemini` routes to `GeminiLLMClient`; `LLM_BACKEND=jobflow-llm` (default) routes
      to `JobflowLLMClient`
- [ ] All unit tests pass: `uv run pytest tests/unit/`
- [ ] All integration tests pass against Docker Compose infra: `uv run pytest tests/integration/`
- [ ] No existing regex/NER extractor tests regressed (path change only)
- [ ] `docker build --platform linux/arm64 .` succeeds in under 10 minutes
- [ ] `.env.example` documents all required env vars with descriptions

## Out of scope

- `enriched_skills` field population (deferred to `jobflow-classifier`)
- `volunteer_experience` and `publications` LLM extraction (low ROI for job matching — kept as
  domain fields, extracted as empty lists until a follow-up task)
- Auth / JWT on the gRPC endpoint — handled at `jobflow-api` layer
- OCI Object Storage adapter for raw PDF persistence (follow-up task)
- Observability / LangFuse tracing instrumentation (follow-up task after service is deployed)
- `jobflow-web` or `jobflow-api` changes — consuming side not touched here

### Subtasks

1. Write contract artifacts (proto + Kafka schema + MCP tool + SQL migration + impact-map update)
2. Expand domain models — ResumeData + ResumeChunk + all domain interfaces (depends on: Write contract artifacts)
3. Restructure into domain/application/infrastructure/api layers — move existing code, delete standalone artifacts, add composition root skeleton (depends on: Expand domain models)
4. Replace Gemini with JobflowLLMClient — BatchedLLMExtractor + ILLMClient + config factory (depends on: Restructure into domain/application/infrastructure/api layers)
5. Add PostgresResumeRepository — asyncpg save + get by user_id (depends on: Restructure into domain/application/infrastructure/api layers)
6. Add QdrantVectorRepository — upsert section chunks to resume_chunks collection (depends on: Restructure into domain/application/infrastructure/api layers)
7. Add Kafka publisher — resume-parsed event (depends on: Restructure into domain/application/infrastructure/api layers)
8. Add gRPC API layer — ParseResume + GetResume servicer, generated stubs from proto (depends on: Write contract artifacts, Restructure into domain/application/infrastructure/api layers)
9. Add MCP tool server — fetch_user_resume via FastMCP (depends on: Add PostgresResumeRepository)
10. Wire ParseResumeUseCase — compose all adapters, chunk → embed → save → upsert → publish (depends on: Replace Gemini with JobflowLLMClient, Add PostgresResumeRepository, Add QdrantVectorRepository, Add Kafka publisher)
11. pyproject.toml + Dockerfile — rename service, update deps, multi-stage ARM64 build with baked GLiNER weights (depends on: Wire ParseResumeUseCase)
12. Update all tests — path changes + new field coverage + mock ILLMClient (depends on: Wire ParseResumeUseCase)
13. Wire main.py composition root — start gRPC + MCP servers with all adapters (depends on: Add gRPC API layer, Add MCP tool server, Wire ParseResumeUseCase, pyproject.toml + Dockerfile)
