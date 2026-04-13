---
task: microservice-conversion
reviewers: developer, qa, compliance, regression, architect, ml-developer, a2a-specialist
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

Embeddings are batched: `IEmbeddingClient.embed_batch(texts) → list[list[float]]` — one MCP call
for all chunks from a single resume rather than one call per chunk.

**Rejected alternatives:**
- _Keep Gemini as a secondary adapter_: unnecessary complexity; no in-project use case for Gemini.
- _Build a new extraction layer from scratch_: the existing regex/NER extractors are correct and
  well-tested; reuse them, keep `ResumeExtractor` as the orchestrator.
- _FastAPI instead of gRPC_: architecture doc mandates gRPC for jobflow-api → resume-service
  (sync, internal waits).
- _Pass raw PDF bytes over gRPC_: gRPC default max message is 4 MB; dense PDFs exceed that; and
  the architecture doc assigns OCI Object Storage to resume-service for PDF storage. jobflow-api
  uploads the file to OCI and passes a storage reference in `ParseResumeRequest`.

**Key design decisions:**

- `ILLMClient` Protocol in `domain/interfaces.py`: `extract_fields(text, fields) → dict`.
  `JobflowLLMClient` (production) calls `jobflow-llm` MCP `/extract`. `GeminiLLMClient` (local
  dev) wraps existing `LLMExtractionStrategy`. Active backend: `LLM_BACKEND` env var.
  Input text truncated to `MAX_LLM_INPUT_CHARS` (config, default 100 000 chars ≈ 25 000 tokens)
  before every call to guard against Gemma 3n context window overflow. Gemma 3n has a 32k-token
  window; 100k chars at ~4 chars/token ≈ 25k tokens, leaving ~7k tokens for the batched prompt
  template and structured output. Character-count truncation is used here (not token-count) as
  a conservative pre-filter — the model-side truncation at `jobflow-llm` is the authoritative
  guard. CJK-heavy resumes are pathological edge cases not targeted in this task (out of scope).

- `IEmbeddingClient` Protocol in `domain/interfaces.py`: `embed_batch(texts: list[str]) →
  list[list[float]]`. Single batched MCP call per resume; `EMBEDDING_MODEL_VERSION` env var pins
  the model; startup check verifies returned vector dimension == 384.

- Batched extraction: `BatchedLLMExtractor` replaces `LLMExtractionStrategy` for all 5 structured
  fields; regex/NER strategies unchanged for name, email, phone, skills, location, URLs.
  The batched prompt instructs the model to return a single top-level JSON object keyed by field
  name: `{"summary": "...", "work_experience": [...], "education": [...], "certifications": [...],
  "projects": [...]}`. Each value uses the existing per-field schema from `_STRUCTURED_SCHEMAS`
  (carried forward from `strategies/llm.py`). Partial-key handling: if a key is absent or null in
  the response, that field is set to `None` (scalars) or `[]` (lists) — same default as the
  current per-field fallback. `BatchedLLMExtractor._parse_response()` iterates expected keys and
  fills missing ones with defaults before returning, so callers never see a `KeyError`.

- `ResumeData` gains `resume_id: UUID`, `user_id: UUID`, `tenant_id: UUID`, `created_at:
  datetime`. Remove `to_dict()` / `to_json()` (serialisation is infrastructure concern).

- `ResumeChunk` domain value object: `{chunk_id, resume_id, user_id, section, text}` — no
  `embedding` field. Infrastructure layer pairs chunks with vectors via `ResumeChunkVector(chunk,
  vector)` inside `QdrantVectorRepository.upsert_chunks()`.

- `GetResume` RPC is keyed by `resume_id` (not `user_id`). Callers needing the latest resume
  for a user call `GetLatestResume(user_id, tenant_id)`. Both RPCs exist; `GetResume` is the
  canonical lookup; `GetLatestResume` is a convenience alias used by the MCP tool internally.

- `ParseResumeRequest` passes `storage_object: string` (OCI Object Storage path) instead of raw
  bytes. jobflow-api uploads the file first; resume-service fetches and parses it. The OCI adapter
  lives in `infrastructure/storage/oci_client.py`. The `IFileStorage` Protocol is in
  `domain/interfaces.py`.

- MCP server lives at `infrastructure/mcp/tools.py` (consistent with jobflow-llm pattern, not
  `api/`). Served on `MCP_PORT` (default 8090). gRPC on `GRPC_PORT` (default 50051). Health HTTP
  on `HTTP_PORT` (default 8080). All three started from `main.py` using `grpc.aio.server()` and
  `asyncio.gather()` — the synchronous `grpc.server()` must not be used as it blocks the event loop.

- MCP `fetch_user_resume` handler calls `GetLatestResumeUseCase` (injected at composition root
  in `main.py`), NOT `PostgresResumeRepository` directly. Calling infrastructure from
  infrastructure violates the hexagonal layer rule in `coding-standards.md`.

- MCP `fetch_user_resume` input includes `tenant_id` to prevent cross-tenant data leaks. Protected
  by `X-Internal-Token` header (value from `INTERNAL_API_TOKEN` env var, injected via k8s Secret).
  Response returns a trimmed agent-facing shape (not full proto dump) — see contract section.

- LangFuse tracing is **deferred** (out of scope for this task; tracked as subtask 16 below).
  All LLM/embed calls use a no-op `TracingClient` stub in this task. The stub has the same
  interface as the real LangFuse client so it can be swapped in subtask 16 without touching
  any call sites.

- `sample_resumes/` renamed to `tests/fixtures/resumes/` — not deleted. Required for integration
  and acceptance tests.

- Rename `services/resume-parser` → `services/resume-service`. The existing `services/resume-
  service/` directory contains stale scaffolding and must be fully deleted before restructuring.
  The stale plan at `services/resume-service/docs/plans/microservice-conversion.md` has already
  been deleted; the remaining directory is deleted as part of subtask 1.

## Interfaces & contracts

| Artifact | Change | File |
|---|---|---|
| `ResumeService.ParseResume` gRPC | create | `contracts/proto/resume.proto` |
| `ResumeService.GetResume` gRPC | create | `contracts/proto/resume.proto` |
| `ResumeService.GetLatestResume` gRPC | create | `contracts/proto/resume.proto` |
| `resume-parsed` Kafka topic + DLQ | create | `contracts/kafka/schemas/resume-parsed.json` |
| `fetch_user_resume` MCP tool | create | `contracts/mcp/tools/fetch-user-resume.json` |
| `resume_service` SQL schema | create | `contracts/migrations/001_resume_service.sql` |
| `impact-map.json` | add `resume-parsed` (producer + known future consumers) + update `fetch-user-resume` | `contracts/impact-map.json` |
| `architecture.md` | add `resume-parsed` row to Kafka topic table; update services table: `resume-service` row from "Python + FastAPI" → "Python + gRPC + FastMCP" | `.claude/architecture.md` |

### Proto — `contracts/proto/resume.proto`

```proto
syntax = "proto3";
package resume;

service ResumeService {
  rpc ParseResume      (ParseResumeRequest)       returns (ParseResumeResponse);
  rpc GetResume        (GetResumeRequest)          returns (GetResumeResponse);
  rpc GetLatestResume  (GetLatestResumeRequest)    returns (GetLatestResumeResponse);
}

message ParseResumeRequest {
  string user_id        = 1;
  string tenant_id      = 2;
  string storage_object = 3;  // OCI Object Storage path: "resumes/<tenant>/<uuid>.pdf"
  string file_name      = 4;  // original filename for format detection
}
message ParseResumeResponse {
  string      resume_id = 1;
  ResumeProto resume    = 2;
}

message GetResumeRequest          { string resume_id = 1; string tenant_id = 2; }
message GetResumeResponse         { ResumeProto resume = 1; }
message GetLatestResumeRequest    { string user_id = 1; string tenant_id = 2; }
message GetLatestResumeResponse   { string resume_id = 1; ResumeProto resume = 2; }

message ResumeProto {
  string resume_id   = 1;
  string user_id     = 2;
  string tenant_id   = 3;
  string name        = 4;
  string email       = 5;
  repeated string skills = 6;
  ContactProto contact   = 7;
  string summary         = 8;
  repeated WorkExperienceProto work_experience  = 9;
  repeated EducationProto      education        = 10;
  repeated CertificationProto  certifications   = 11;
  repeated ProjectProto        projects         = 12;
  repeated string interests  = 13;
  repeated string languages  = 14;
  repeated string awards     = 15;
  string created_at = 16;  // ISO-8601
}

message ContactProto {
  string phone         = 1;
  string location      = 2;
  string linkedin_url  = 3;
  string github_url    = 4;
  string portfolio_url = 5;
  repeated string other_urls = 6;
}

message WorkExperienceProto {
  string company          = 1;
  string title            = 2;
  string location         = 3;
  string start_date       = 4;
  string end_date         = 5;
  int32  duration_months  = 6;
  string description      = 7;
  repeated string responsibilities = 8;
  repeated string skills_used      = 9;
}

message EducationProto {
  string institution    = 1;
  string degree         = 2;
  string field_of_study = 3;
  string start_date     = 4;
  string end_date       = 5;
  float  gpa            = 6;
  string honors         = 7;
}

message CertificationProto {
  string name                 = 1;
  string issuing_organization = 2;
  string issue_date           = 3;
  string expiry_date          = 4;
  string credential_id        = 5;
  string credential_url       = 6;
}

message ProjectProto {
  string          name         = 1;
  string          description  = 2;
  repeated string technologies = 3;
  string          url          = 4;
  string          start_date   = 5;
  string          end_date     = 6;
}
```

### Kafka — `resume-parsed` schema

```json
{
  "event": "resume-parsed",
  "resume_id": "<uuid>",
  "user_id": "<uuid>",
  "tenant_id": "<uuid>",
  "created_at": "<iso8601>"
}
```

Producer: `resume-service`. DLQ: `resume-parsed.DLQ`.
Consumers at contract time: none. Future consumers: `jobflow-matcher`, `jobflow-application`.

### MCP — `fetch_user_resume` contract (`contracts/mcp/tools/fetch-user-resume.json`)

```json
{
  "name": "fetch_user_resume",
  "description": "Fetch the user's latest parsed resume as a structured summary for content generation. Returns trimmed agent-facing shape — not the full proto.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "user_id":   { "type": "string", "format": "uuid" },
      "tenant_id": { "type": "string", "format": "uuid" }
    },
    "required": ["user_id", "tenant_id"]
  },
  "outputSchema": {
    "type": "object",
    "required": ["resume_id", "name", "skills", "experience", "education"],
    "properties": {
      "resume_id": { "type": "string" },
      "name":      { "type": "string" },
      "summary":   { "type": "string" },
      "skills":    { "type": "array", "items": { "type": "string" } },
      "experience": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "title":           { "type": "string" },
            "company":         { "type": "string" },
            "responsibilities": { "type": "array", "items": { "type": "string" } },
            "skills_used":     { "type": "array", "items": { "type": "string" } }
          }
        }
      },
      "education": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "degree":      { "type": "string" },
            "institution": { "type": "string" }
          }
        }
      }
    }
  }
}

```

Auth: `X-Internal-Token` header required (value from `INTERNAL_API_TOKEN` k8s Secret).

### SQL — `contracts/migrations/001_resume_service.sql`

```sql
CREATE TABLE resumes (
  resume_id  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    UUID        NOT NULL,
  tenant_id  UUID        NOT NULL,
  name       TEXT,
  email      TEXT,
  raw_text   TEXT        NOT NULL,
  parsed_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_resumes_user_tenant ON resumes (user_id, tenant_id);
CREATE INDEX idx_resumes_tenant      ON resumes (tenant_id);
```

`resume_sections` table is **not** created. The `resumes` table is the **sole source of truth**
for `GetResume` and `GetLatestResume`. Both RPCs reconstruct `ResumeProto` entirely from Postgres
scalar fields. Qdrant is write-only from the read-path perspective — it stores vectors for
jobflow-matcher's similarity search; its data is not read by `GetResume`. If Qdrant is
unavailable, `GetResume` still returns the full resume. The structured section fields
(work_experience, education, etc.) must be stored as JSONB columns in the `resumes` table so they
can be reconstructed without Qdrant.

Add to migration:
```sql
ALTER TABLE resumes ADD COLUMN parsed_data JSONB;  -- stores full ResumeData structured fields
```

### impact-map.json changes

```json
"contracts/kafka/schemas/resume-parsed.json":  ["jobflow-matcher", "jobflow-application"],
"contracts/mcp/tools/fetch-user-resume.json":  ["jobflow-application"]
```

Note: `resume-service` is the **producer** of `resume-parsed`; it does NOT appear as a consumer.
`resume-service` is the MCP server (producer) of `fetch_user_resume`; it does NOT appear as a
consumer of that contract either. Only downstream consumers are listed.

### architecture.md addition — Kafka topic table row

```
| resume-parsed | resume-service | jobflow-matcher, jobflow-application (built in later tasks) | resume-parsed.DLQ |
```

## Files to change

### Deleted
| File | Action |
|---|---|
| `services/resume-parser/examples.py` | delete |
| `services/resume-parser/README.md` | delete |
| `services/resume-parser/TESTING.md` | delete |
| `services/resume-parser/src/parsers/tests/generate_test_pdfs.py` | delete |
| `services/resume-parser/src/parsers/tests/generate_test_data.py` | delete |

### Moved
| From | To |
|---|---|
| `services/resume-parser/sample_resumes/` | `services/resume-service/tests/fixtures/resumes/` |

### New contract files
| File | Action |
|---|---|
| `contracts/proto/resume.proto` | create |
| `contracts/kafka/schemas/resume-parsed.json` | create |
| `contracts/mcp/tools/fetch-user-resume.json` | create |
| `contracts/migrations/001_resume_service.sql` | create |
| `contracts/impact-map.json` | modify |
| `.claude/architecture.md` | modify (add resume-parsed Kafka row; update resume-service row to "Python + gRPC + FastMCP") |

### Service — rename + restructure (services/resume-parser → services/resume-service)
| File | Action | What changes |
|---|---|---|
| `services/resume-service/src/domain/models.py` | create | Consolidates existing `models/`; adds `resume_id`, `user_id`, `tenant_id`, `created_at`; adds `ResumeChunk` (no embedding field); removes `to_dict`/`to_json` |
| `services/resume-service/src/domain/interfaces.py` | create | `IResumeRepository`, `IVectorRepository`, `ILLMClient`, `IEmbeddingClient`, `IEventPublisher`, `IFileParser`, `IFileStorage`, `ITracingClient` Protocols |
| `services/resume-service/src/domain/exceptions.py` | create | Consolidates existing `exceptions/` |
| `services/resume-service/src/application/use_cases.py` | create | `ParseResumeUseCase` — fetch from OCI → parse → extract → embed_batch → save(Postgres JSONB) → upsert(Qdrant) → publish; `GetLatestResumeUseCase` — reads from `IResumeRepository` only, no Qdrant dependency |
| `services/resume-service/src/infrastructure/llm/jobflow_client.py` | create | `JobflowLLMClient(ILLMClient)` — calls `jobflow-llm` MCP `/extract`; truncates input to `MAX_LLM_INPUT_CHARS` |
| `services/resume-service/src/infrastructure/llm/gemini_client.py` | create | `GeminiLLMClient(ILLMClient)` — local dev fallback |
| `services/resume-service/src/infrastructure/llm/config.py` | create | `build_llm_client(settings) → ILLMClient`; reads `LLM_BACKEND` |
| `services/resume-service/src/infrastructure/embedding/jobflow_client.py` | create | `JobflowEmbeddingClient(IEmbeddingClient)` — calls `jobflow-llm` MCP `/embed` with all texts in one request |
| `services/resume-service/src/infrastructure/embedding/config.py` | create | `build_embedding_client(settings) → IEmbeddingClient` |
| `services/resume-service/src/infrastructure/tracing/stub.py` | create | No-op `TracingClientStub(ITracingClient)` — wraps LLM/embed calls; swappable for real LangFuse later |
| `services/resume-service/src/infrastructure/storage/oci_client.py` | create | `OCIStorageClient(IFileStorage)` — fetches object by path from OCI Object Storage |
| `services/resume-service/src/infrastructure/postgres/repository.py` | create | `PostgresResumeRepository(IResumeRepository)` — asyncpg; `save(resume)` stores full `parsed_data` as JSONB; `get_by_id(resume_id, tenant_id)` + `get_latest_by_user(user_id, tenant_id)` — Postgres only, no Qdrant |
| `services/resume-service/src/infrastructure/qdrant/repository.py` | create | `QdrantVectorRepository(IVectorRepository)` — `upsert_chunks(chunks: list[ResumeChunkVector])` only; write-only from read-path perspective; no GetResume dependency |
| `services/resume-service/src/infrastructure/qdrant/models.py` | create | `ResumeChunkVector(chunk: ResumeChunk, vector: list[float])` — infrastructure-only value object |
| `services/resume-service/src/infrastructure/kafka/publisher.py` | create | `KafkaEventPublisher(IEventPublisher)` — aiokafka; publishes `resume-parsed` |
| `services/resume-service/src/infrastructure/parsers/pdf.py` | create | Move + rename `src/parsers/pdf_parser.py` |
| `services/resume-service/src/infrastructure/parsers/word.py` | create | Move + rename `src/parsers/word_parser.py` |
| `services/resume-service/src/infrastructure/extractors/` | create | Move existing `extractors/` tree; replace `LLMExtractionStrategy` with `BatchedLLMExtractor`; add NER truncation guard in `strategies/ner.py`: read token limit via `getattr(model.config, 'max_len', 384)` — for `urchade/gliner_multi_pii-v1` this resolves to 384 (confirmed in `gliner_config.json`). Use `model.data_processor.transformer_tokenizer.encode()` to tokenize and slice to that limit before passing to `predict_entities()`. Fallback of 384 is the actual model value, not an approximation. Do NOT use `model.config.max_position_embeddings` (backbone attribute, not the GLiNER-level limit). |
| `services/resume-service/src/infrastructure/mcp/tools.py` | create | FastMCP server on `MCP_PORT`; exposes `fetch_user_resume`; validates `X-Internal-Token`; calls `GetLatestResumeUseCase` injected from composition root |
| `services/resume-service/src/api/grpc/server.py` | create | gRPC servicer on `GRPC_PORT`; calls use case; maps domain ↔ proto |
| `services/resume-service/src/api/grpc/generated/` | create | Output of `python -m grpc_tools.protoc` on `resume.proto` |
| `services/resume-service/src/config.py` | create | Pydantic `Settings`; all env vars; startup dim-check: call `embed_batch(["test"])`, assert `len(result[0]) == settings.expected_embedding_dim` (from `EXPECTED_EMBEDDING_DIM` env var, default 384) |
| `services/resume-service/src/main.py` | create | Composition root; starts gRPC (50051) + MCP (8090) + health HTTP (8080) |
| `services/resume-service/pyproject.toml` | create | Rename to `resume-service`; required: `grpcio`, `grpcio-tools`, `asyncpg`, `qdrant-client`, `aiokafka`, `fastmcp`, `sentence-transformers`, `pydantic-settings`, `oci-python-sdk`; optional `google-generativeai` (dev extra) |
| `services/resume-service/Dockerfile` | create | Multi-stage, `--platform linux/arm64`; pre-bakes GLiNER weights; `EXPOSE 50051 8090 8080` |
| `services/resume-service/.env.example` | create | All env vars with descriptions |

### Tests
| File | Action |
|---|---|
| `services/resume-service/tests/unit/test_use_cases.py` | create | `ParseResumeUseCase` + `GetLatestResumeUseCase` unit tests |
| `services/resume-service/tests/unit/test_batched_extractor.py` | create | `BatchedLLMExtractor` + `JobflowEmbeddingClient` (embed_batch single-call) |
| `services/resume-service/tests/unit/test_domain_models.py` | create | `ResumeData`, `ResumeChunk` model tests |
| `services/resume-service/tests/unit/test_parsers.py` | create | PDF + Word parser tests |
| `services/resume-service/tests/unit/test_extractors.py` | create | Regex/NER extractor tests + NER truncation test |
| `services/resume-service/tests/unit/test_config.py` | create | `test_startup_fails_on_wrong_embedding_dims()` + LLM backend factory tests |
| `services/resume-service/tests/integration/test_grpc_server.py` | create | gRPC round-trip with fixture PDF |
| `services/resume-service/tests/integration/test_postgres_repository.py` | create | asyncpg against Docker Postgres |
| `services/resume-service/tests/integration/test_qdrant_repository.py` | create | qdrant-client against Docker Qdrant |
| `services/resume-service/tests/integration/test_mcp_server.py` | create | MCP auth + fetch_user_resume response shape + cross-tenant isolation |
| `services/resume-service/tests/integration/test_kafka_publisher.py` | create | resume-parsed event schema verification |
| `services/resume-service/tests/fixtures/resumes/` | move from `sample_resumes/` | Fixture PDFs for integration tests |

## Test strategy

**Unit — `ParseResumeUseCase`** (`tests/unit/test_use_cases.py`):
- `test_parse_resume_happy_path()` — all adapters succeed; `ParseResumeResponse` populated
- `test_parse_resume_llm_failure_returns_partial_data()` — `ILLMClient` raises; structured fields
  are `None`; non-LLM fields still populated; event still published (partial data is acceptable)
- `test_parse_resume_qdrant_failure_raises()` — `IVectorRepository` raises; use case propagates;
  Postgres write is rolled back (or left and flagged — implementer decides and documents)
- `test_parse_resume_kafka_failure_logs_and_raises()` — `IEventPublisher` raises; use case
  propagates; resume already saved to Postgres (partially complete — acceptable for retry)
- `test_parse_resume_storage_fetch_failure_raises()` — `IFileStorage` raises; no downstream calls

**Unit — `BatchedLLMExtractor`** (`tests/unit/test_batched_extractor.py`):
- `test_batched_extract_returns_all_5_fields()`
- `test_batched_extract_partial_response_fills_none()`
- `test_batched_extract_malformed_json_raises()`
- `test_batched_extract_truncates_input_at_max_chars()` — input > `MAX_LLM_INPUT_CHARS` is trimmed

**Unit — `JobflowEmbeddingClient`** (`tests/unit/test_batched_extractor.py`):
- `test_embed_batch_single_call_for_multiple_texts()` — mock verifies only one MCP call for N texts

**Unit — config factory + startup check** (`tests/unit/test_config.py`):
- `test_build_llm_client_defaults_to_jobflow()`
- `test_build_llm_client_gemini_selected_by_env()`
- `test_startup_fails_on_wrong_embedding_dims()` — mock `embed_batch` returns 256-dim vector; assert startup raises `RuntimeError`

**Unit — domain models** (`tests/unit/test_domain_models.py`):
- `test_resume_data_requires_tenant_id()`
- `test_resume_chunk_has_no_embedding_field()`

**Unit — NER truncation** (`tests/unit/test_extractors.py`, class `TestNERExtractionStrategy`):
- `test_ner_strategy_truncates_input_exceeding_model_max_tokens()` — input that would exceed 384
  tokens is truncated to `getattr(model.config, 'max_len', 384)` tokens using
  `model.data_processor.transformer_tokenizer.encode()` before `predict_entities()` is called;
  mock verifies the truncated token sequence is passed, not the original long text; also verifies
  fallback to 384 when `model.config.max_len` is not present

**Integration — `PostgresResumeRepository`**:
- `test_save_and_get_resume_round_trip()`
- `test_get_latest_resume_returns_most_recent()`
- `test_get_resume_not_found_returns_none()`

**Integration — `QdrantVectorRepository`**:
- `test_upsert_and_query_chunks()`

**Integration — gRPC server** (`tests/integration/test_grpc_server.py`):
- `test_parse_resume_grpc_returns_populated_response()` — uses fixture PDF from `tests/fixtures/`

**Integration — MCP token auth + tenant isolation**:
- `test_fetch_user_resume_rejects_missing_token()` — no `X-Internal-Token` → 401
- `test_fetch_user_resume_accepts_valid_token()` — correct token → resume data returned
- `test_fetch_user_resume_rejects_wrong_tenant()` — valid token, real `user_id`, but `tenant_id`
  belonging to a different tenant → empty/null result (not the other tenant's resume). Asserts
  multi-tenant PII isolation at the MCP layer.

**Integration — Kafka publish verification**:
- `test_resume_parsed_event_published_with_correct_schema()` — test subscribes to `resume-parsed`
  topic after parse; verifies event fields match `contracts/kafka/schemas/resume-parsed.json`

## Acceptance criteria

- [ ] `ParseResume` gRPC call with a real PDF (from `tests/fixtures/resumes/`) returns populated
      `ParseResumeResponse` with name, email, skills, at least one work entry
- [ ] `GetResume(resume_id)` returns the previously saved resume
- [ ] `GetLatestResume(user_id, tenant_id)` returns the most recent resume for the user
- [ ] `fetch_user_resume` MCP tool (with valid `X-Internal-Token`) returns trimmed resume matching
      `outputSchema` in `fetch-user-resume.json`; call without token returns 401
- [ ] `resume-parsed` Kafka event published after successful parse; event schema matches
      `contracts/kafka/schemas/resume-parsed.json`
- [ ] `LLM_BACKEND=gemini` routes to `GeminiLLMClient`; unset/`jobflow-llm` routes to
      `JobflowLLMClient`
- [ ] Startup fails (exception logged, pod exits 1) if `embed_batch(["test"])` returns vector ≠ 384
      dimensions; verified by `test_startup_fails_on_wrong_embedding_dims()` in
      `tests/unit/test_config.py` with a mock returning a 256-dim vector
- [ ] All unit tests pass: `uv run pytest tests/unit/`
- [ ] All integration tests pass against Docker Compose infra: `uv run pytest tests/integration/`
- [ ] No existing regex/NER extractor tests regressed
- [ ] `docker build --platform linux/arm64 .` succeeds
- [ ] `.env.example` has every env var listed in `config.py`

## Environment variables (all required unless marked optional)

| Var | Example | Purpose |
|---|---|---|
| `GRPC_PORT` | `50051` | gRPC server port |
| `MCP_PORT` | `8090` | FastMCP server port |
| `HTTP_PORT` | `8080` | Health check HTTP port |
| `DATABASE_URL` | `postgresql+asyncpg://...` | Postgres connection |
| `QDRANT_URL` | `http://qdrant:6333` | Qdrant connection |
| `KAFKA_BOOTSTRAP_SERVERS` | `redpanda:9092` | Kafka brokers |
| `OCI_STORAGE_BUCKET` | `jobflow-resumes` | OCI Object Storage bucket |
| `OCI_CONFIG_FILE` | `/etc/oci/config` | OCI SDK config path |
| `LLM_BACKEND` | `jobflow-llm` | `jobflow-llm` or `gemini` |
| `JOBFLOW_LLM_MCP_URL` | `http://jobflow-llm:8080/mcp` | jobflow-llm MCP endpoint |
| `MAX_LLM_INPUT_CHARS` | `100000` | LLM input char truncation limit (≈25k tokens at 4 chars/token; leaves headroom for prompt + output in Gemma 3n 32k-token window) |
| `EMBEDDING_MODEL_VERSION` | `sentence-transformers/all-MiniLM-L6-v2` | Must match jobflow-classifier |
| `EXPECTED_EMBEDDING_DIM` | `384` | Expected output dimension for startup dim-check; fails startup if `embed_batch(["test"])` returns vectors of a different length. Derived from the model: all-MiniLM-L6-v2 = 384. Must be updated if embedding model changes. |
| `INTERNAL_API_TOKEN` | `<secret>` | Shared bearer token for MCP auth (from k8s Secret) |
| `GEMINI_API_KEY` | _(optional, dev only)_ | Required only when `LLM_BACKEND=gemini` |

## Out of scope

- `enriched_skills` population (deferred to `jobflow-classifier`)
- `volunteer_experience` and `publications` LLM extraction (extracted as empty lists)
- Auth / JWT on the gRPC endpoint — handled at `jobflow-api` layer
- LangFuse tracing — `ITracingClient` stub added now; real client wired in subtask 16
- `jobflow-web` or `jobflow-api` changes — consuming side not touched here

### Subtasks

1. Write contract artifacts (proto + Kafka schema + MCP tool + SQL migration + impact-map update + architecture.md Kafka row + architecture.md services table: resume-service "Python + FastAPI" → "Python + gRPC + FastMCP") — also delete stale `services/resume-service/` directory before any restructuring begins
2. Expand domain models — ResumeData + ResumeChunk (no embedding) + all domain interfaces including IEmbeddingClient + IFileStorage (depends on: Write contract artifacts)
3. Restructure into domain/application/infrastructure/api layers — move existing code, delete standalone artifacts, move sample_resumes to tests/fixtures, add composition root skeleton (depends on: Expand domain models)
4. Replace Gemini with JobflowLLMClient — BatchedLLMExtractor + ILLMClient + config factory + MAX_LLM_INPUT_CHARS truncation + NER 2000-char guard (depends on: Restructure into domain/application/infrastructure/api layers)
5. Add JobflowEmbeddingClient — embed_batch batched MCP call + startup dim-check (depends on: Restructure into domain/application/infrastructure/api layers)
6. Add PostgresResumeRepository — asyncpg save + get_by_id + get_latest_by_user (depends on: Restructure into domain/application/infrastructure/api layers)
7. Add QdrantVectorRepository — upsert ResumeChunkVector (write-only; no GetResume dependency; Qdrant unavailability must not affect read RPCs) (depends on: Restructure into domain/application/infrastructure/api layers)
8. Add Kafka publisher — resume-parsed event with tenant_id (depends on: Restructure into domain/application/infrastructure/api layers)
9. Add OCI storage client — fetch object by path (depends on: Restructure into domain/application/infrastructure/api layers)
10. Add gRPC API layer — ParseResume + GetResume + GetLatestResume servicer, generated stubs from proto (depends on: Write contract artifacts, Restructure into domain/application/infrastructure/api layers)
11. Add MCP tool server — fetch_user_resume via FastMCP on MCP_PORT with X-Internal-Token auth, trimmed response shape (depends on: Add PostgresResumeRepository, Add QdrantVectorRepository)
12. Wire ParseResumeUseCase — compose all adapters: OCI fetch → parse → extract → embed_batch → save → upsert → publish (depends on: Replace Gemini with JobflowLLMClient, Add JobflowEmbeddingClient, Add PostgresResumeRepository, Add QdrantVectorRepository, Add Kafka publisher, Add OCI storage client)
13. pyproject.toml + Dockerfile — rename service, update deps, multi-stage ARM64 build with baked GLiNER weights, EXPOSE 50051 8090 8080 (depends on: Wire ParseResumeUseCase)
14. Update all tests — path changes + new field coverage + mock ILLMClient + mock IEmbeddingClient + MCP auth tests + Kafka publish verification (depends on: Wire ParseResumeUseCase)
15. Wire main.py composition root — start gRPC + MCP + health servers with all adapters (depends on: Add gRPC API layer, Add MCP tool server, Wire ParseResumeUseCase, pyproject.toml + Dockerfile)
16. Wire LangFuse tracing — replace no-op TracingClientStub with real LangFuse client in LangfuseTracingClient(ITracingClient); add LANGFUSE_PUBLIC_KEY + LANGFUSE_SECRET_KEY + LANGFUSE_HOST env vars (depends on: Wire main.py composition root)
