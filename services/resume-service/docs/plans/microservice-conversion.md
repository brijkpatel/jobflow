# Task: resume-service microservice conversion

reviewers: developer, qa, compliance, regression, architect, ml-developer

## Overview

Convert the standalone resume-parser library into a production-ready microservice within the jobflow monorepo. The service exposes a gRPC API, persists to Postgres, publishes Kafka events, generates embeddings via jobflow-llm, and replaces the Gemini dependency with jobflow-llm HTTP calls.

## Current state

- File parsers (PDF, Word) — keep as-is, relocate
- Strategy pattern extractors (Regex, NER, LLM) — keep Regex + NER, replace LLM
- `ResumeData` model — only name/email/skills, massively incomplete
- `ResumeExtractor` fallback coordinator — keep pattern, refactor
- `ResumeParserFramework` top-level entry — dissolve into application layer
- No API, no DB, no Kafka, no embeddings, no Dockerfile

## Target structure

```
services/resume-service/
  src/
    domain/
      models/          # ResumeData, Experience, Education, Certification, Project, ResumeChunk
      interfaces/      # Protocol: FileParser, ExtractionStrategy, ResumeRepository, LLMClient, EmbeddingClient, VectorRepository
      exceptions/      # domain exceptions (no framework imports)
    application/
      parse_resume.py  # ParseResumeUseCase — orchestrates parse → extract → chunk+embed → store → upsert Qdrant → publish
    infrastructure/
      parsers/         # PDFParser, WordParser (pdfminer, python-docx)
      extractors/      # strategies: regex.py, ner.py (GLiNER singleton), llm_client.py (calls jobflow-llm)
      db/              # PostgresResumeRepository (asyncpg)
      llm/             # JobflowLLMClient (HTTP → jobflow-llm /extract, /embed — LangFuse traced)
      vector/          # QdrantVectorRepository (qdrant-client → resume_chunks collection)
      kafka/           # ResumeEventPublisher (aiokafka)
      mcp/             # fetch_user_resume MCP tool server
    api/
      grpc/            # ResumeServicer (grpc) — ParseResume, GetResume handlers
      health.py        # HTTP GET /health → {"status":"ok"} (k8s liveness/readiness)
    main.py            # composition root — wires all interfaces to implementations
  pyproject.toml
  Dockerfile           # GLiNER weights baked in (no runtime HuggingFace download)
  .env.example
```

## Domain model changes

### ResumeData (expanded)

```python
@dataclass
class Experience:
    company: str
    title: str
    start_date: str          # ISO: "2022-03"
    end_date: Optional[str]  # None = current
    location: Optional[str]
    bullets: List[str]

@dataclass
class Education:
    institution: str
    degree: str
    field: Optional[str]
    graduation_date: Optional[str]
    gpa: Optional[float]

@dataclass
class Certification:
    name: str
    issuer: Optional[str]
    date: Optional[str]

@dataclass
class Project:
    name: str
    description: Optional[str]
    technologies: List[str]

@dataclass
class ResumeData:
    # Contact
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    location: Optional[str]
    linkedin_url: Optional[str]
    github_url: Optional[str]
    portfolio_url: Optional[str]
    # Content
    summary: Optional[str]
    skills: List[str]
    experience: List[Experience]
    education: List[Education]
    certifications: List[Certification]
    languages: List[str]
    projects: List[Project]
    # Computed
    years_of_experience: Optional[float]  # derived from experience dates
```

### Domain interfaces (Protocol)

```python
class FileParser(Protocol):
    def parse(self, file_bytes: bytes, filename: str) -> str: ...

class ExtractionStrategy(Protocol[T]):
    def extract(self, text: str) -> T: ...

class ResumeRepository(Protocol):
    async def save(self, resume: ResumeData, tenant_id: str, user_id: str) -> str: ...  # returns resume_id
    async def get(self, resume_id: str, tenant_id: str) -> Optional[ResumeData]: ...

class LLMClient(Protocol):
    # Single batched call for all LLM fields — never called per-field
    async def extract_fields(self, text: str, fields: List[str]) -> dict: ...

class EmbeddingClient(Protocol):
    async def embed(self, text: str) -> List[float]: ...  # called per chunk, not per resume

class VectorRepository(Protocol):
    async def upsert_chunks(self, resume_id: str, user_id: str, tenant_id: str, chunks: List[ResumeChunk]) -> None: ...
```

## Application layer

### ParseResumeUseCase

```
Input: file_bytes, filename, tenant_id, user_id
Steps:
  1. Select parser by file extension
  2. Parse file → raw text
  3a. Extract simple fields synchronously — regex/NER: name, email, phone, linkedin_url, github_url
  3b. Extract all LLM fields in ONE batched call to jobflow-llm /extract:
      fields=["summary", "skills", "experience", "education", "certifications", "projects"]
      → returns dict, fan out to domain model
  4. Compute years_of_experience from experience dates
  5. Build resume chunks for embedding:
      chunks = [summary_text, skills_text, *[exp bullets joined], *[edu entries], ...]
      Each chunk: {section_type, text, chunk_index}
  6. Embed each chunk via EmbeddingClient.embed(chunk.text) → vector
      (one HTTP call per chunk to jobflow-llm /embed, LangFuse traced)
  7. Call ResumeRepository.save(resume, tenant_id, user_id) → resume_id
  8. Call VectorRepository.upsert_chunks(resume_id, user_id, tenant_id, chunks_with_vectors)
      → upserts to Qdrant resume_chunks collection with payload {resume_id, user_id, tenant_id, section_type}
  9. Publish resume-parsed Kafka event {resume_id, user_id, tenant_id, chunk_count, parsed_at}
  10. Return ResumeData + resume_id
```

## LLM strategy → jobflow-llm

Replace `google.generativeai` with HTTP calls to `jobflow-llm` service via `httpx.AsyncClient`.
All calls wrapped with LangFuse traces (tenant_id, latency, token counts).

```python
class JobflowLLMClient:
    async def extract_fields(self, text: str, fields: List[str]) -> dict:
        # Single POST — all LLM fields in one call, never per-field
        # POST http://jobflow-llm/extract
        # body: {text, fields: ["summary", "skills", "experience", "education", "certifications", "projects"]}
        # returns: {summary: "...", skills: [...], experience: [...], ...}

class JobflowEmbeddingClient:
    async def embed(self, text: str) -> List[float]:
        # POST http://jobflow-llm/embed
        # body: {text, model: EMBEDDING_MODEL_VERSION}
        # returns: {vector: [float, ...]}  # 384-dim
        # LangFuse traced: section chunk latency + model version
```

All structured extraction (experience, education, certifications, projects, summary, skills) goes through one batched LLM call. Simple fields (name, email, phone, URLs) keep regex/NER strategies.

## Extraction strategy per field

| Field | Primary | Fallback |
|---|---|---|
| name | NER | LLM |
| email | regex | NER |
| phone | regex | NER |
| linkedin_url | regex | — |
| github_url | regex | — |
| summary | LLM | — |
| skills | LLM | NER |
| experience | LLM | — |
| education | LLM | — |
| certifications | LLM | — |
| languages | NER | LLM |
| projects | LLM | — |

## gRPC API

Matches `contracts/proto/resume.proto`:

```
rpc ParseResume(ParseResumeRequest) → ParseResumeResponse
  request:  file_bytes, filename, tenant_id
  response: resume_id, resume (ResumeData as proto message)

rpc GetResume(GetResumeRequest) → GetResumeResponse
  request:  resume_id, tenant_id
  response: resume (ResumeData as proto message)
```

## Kafka event

Topic: `resume-parsed`
Schema: `{resume_id, user_id, tenant_id, chunk_count, parsed_at}`

Note: vector is NOT included — it is already stored in Qdrant (step 8 of use case). Publishing 384 floats over Kafka is an anti-pattern.

## Environment variables

```env
# Service
GRPC_PORT=50051
HTTP_PORT=8080          # health only (HTTP JSON: GET /health → {"status":"ok"})

# Infra (shared across services, injected by Helm)
DATABASE_URL=postgresql+asyncpg://...
KAFKA_BOOTSTRAP_SERVERS=redpanda:9092
QDRANT_URL=http://qdrant:6333

# jobflow-llm (internal service URL)
LLM_SERVICE_URL=http://jobflow-llm:8000

# Embedding — MUST match EMBEDDING_MODEL_VERSION in jobflow-classifier exactly (Qdrant breaks silently if they differ)
EMBEDDING_MODEL_VERSION=sentence-transformers/all-MiniLM-L6-v2

# Observability
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_SECRET_KEY=...
LANGFUSE_HOST=http://langfuse:3000
```

No `GEMINI_API_KEY`. No `python-dotenv` in production (env injected by k8s).

## Dependencies (pyproject.toml)

```toml
[project]
dependencies = [
    "grpcio", "grpcio-tools",
    "asyncpg",
    "aiokafka",
    "pdfminer.six",
    "python-docx",
    "gliner",          # NER — singleton, loaded once at startup, weights baked into Docker image
    "httpx",           # async HTTP for jobflow-llm calls
    "qdrant-client",   # Qdrant upsert for resume_chunks collection
    "langfuse",        # trace all LLM + embedding calls
    "pydantic",        # config validation
]

[dependency-groups]
dev = ["pytest", "pytest-asyncio", "pytest-mock"]
```

## Dockerfile

```dockerfile
FROM python:3.12-slim AS builder
# ARM64-compatible, no platform emulation needed on Oracle Ampere A1
RUN pip install uv
WORKDIR /app
COPY pyproject.toml .
RUN uv sync --no-dev
# Bake GLiNER model weights into image — no runtime HuggingFace download
# (avoids cold-start failures when egress to HuggingFace is blocked in k8s)
RUN python -c "from gliner import GLiNER; GLiNER.from_pretrained('urchade/gliner_multi_pii-v1')"
COPY src/ src/

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /app /app
COPY --from=builder /root/.cache/huggingface /root/.cache/huggingface
EXPOSE 50051 8080
# Single process — GLiNER (~500MB) + runtime overhead fits within 1.5GB ARM pod limit.
# Do NOT add --workers N: each worker would load a separate GLiNER instance, exceeding the budget.
CMD ["python", "-m", "src.main"]
```

GLiNER is instantiated once at application startup as a shared singleton — never per-request.
Helm chart must set `resources.limits.memory: 1.5Gi` and `resources.requests.memory: 1Gi` for this service.

## What is NOT changing

- PDF + Word parser logic (just relocated)
- Regex patterns for email, phone, URLs
- NER strategy using gliner (just relocated)
- Exception class hierarchy (moved to domain/)
- Fallback chain logic in coordinator (moved to application/)
- Existing tests (paths update, new tests added for new fields)

## Contract artifacts this task must produce

All of these must be written as part of this task (subtask 1) and require architect review before merging:

1. `contracts/proto/resume.proto` — ResumeService (ParseResume, GetResume) with full ResumeData message including all new fields
2. `contracts/kafka/schemas/resume-parsed.json` — schema: `{resume_id, user_id, tenant_id, chunk_count, parsed_at}`
3. `contracts/mcp/tools/fetch-user-resume.json` — MCP tool definition consumed by jobflow-application ADK agent
4. Update `contracts/impact-map.json`:
   - `contracts/proto/resume.proto` → `["resume-service", "jobflow-api"]`
   - `contracts/kafka/schemas/resume-parsed.json` → `["resume-service", "jobflow-matcher"]`
   - `contracts/mcp/tools/fetch-user-resume.json` → `["resume-service", "jobflow-application"]`

### Subtasks

1. Write contract artifacts (proto + Kafka schema + MCP tool + impact-map update)
2. Expand domain models (ResumeData + sub-models + ResumeChunk + all domain interfaces including VectorRepository)
3. Restructure into domain/application/infrastructure/api layers — move existing code, add main.py composition root
4. Replace Gemini with JobflowLLMClient — single batched /extract call for all 5 LLM fields, LangFuse traced (depends on: Restructure into domain/application/infrastructure/api layers)
5. Add extraction for missing fields — experience, education, certifications, projects, summary, phone, URLs (depends on: Replace Gemini with JobflowLLMClient)
6. Add PostgresResumeRepository (asyncpg) (depends on: Restructure into domain/application/infrastructure/api layers)
7. Add QdrantVectorRepository — upsert section chunks to resume_chunks collection (depends on: Expand domain models)
8. Add gRPC API layer — ParseResume + GetResume, generated from proto in subtask 1 (depends on: Write contract artifacts, Restructure into domain/application/infrastructure/api layers)
9. Add MCP tool server — fetch_user_resume (depends on: Write contract artifacts, Add PostgresResumeRepository)
10. Add Kafka publisher — resume-parsed event with user_id (depends on: Add PostgresResumeRepository)
11. Wire ParseResumeUseCase — chunk → embed → save → upsert → publish (depends on: Add extraction for missing fields, Add PostgresResumeRepository, Add QdrantVectorRepository, Add Kafka publisher)
12. pyproject.toml + Dockerfile with baked GLiNER weights
13. Update all tests — path changes + new field coverage + mock jobflow-llm client
