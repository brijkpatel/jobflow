# jobflow-llm

LiteRT-LM inference service. Exposes a single MCP endpoint consumed by all other services. No A2A, no Kafka — pure inference gateway.

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
- `src/domain/` — GenerateRequest, GenerateResponse, EmbedRequest, EmbedResponse
- `src/application/` — GeneratePipeline, EmbedPipeline
- `src/infrastructure/litert/` — LiteRT-LM runtime (Gemma 3n quantized)
- `src/infrastructure/mcp/` — MCP tool server (generate, embed)

## Protocols
- **Exposes:** MCP tools (consumed by all services)
  - `generate(prompt, system_prompt, max_tokens, temperature) → text`
  - `embed(texts[]) → vectors[][]`
  - `tailor_resume(resume, job_description, emphasis_areas) → tailored_resume`
  - `cover_letter(resume, job_description, company_context) → cover_letter`
  - `qa_answers(questions[], resume, company_context) → answers[]`
  - `score_content(content, job_description, rubric) → {score, feedback[]}`

## Key rules
- `JOBFLOW_MODEL_VERSION` env var controls which Gemma 3n checkpoint to load
- Model weights baked into Docker image at build time — no runtime download
- Single-worker process (model is too large for multi-process fork)
- KEDA scales on MCP request queue depth (min 1 — always at least one replica, max 5)
- All calls traced via LangFuse with tenant_id, latency, token counts
- Embedding model version: `EMBEDDING_MODEL_VERSION=sentence-transformers/all-MiniLM-L6-v2`
  — must match the version used in resume-service and jobflow-classifier
- See `.claude/architecture.md` for MCP tool contracts
