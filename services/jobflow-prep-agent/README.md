# jobflow-prep-agent

Two agents in one service: **InterviewPrepAgent** (async per-application) and **ProfileOptimizerAgent** (weekly batch CronJob).

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
- `src/domain/` — PrepPack entity, OptimizationReport entity, interfaces
- `src/application/` — InterviewPrepPipeline (ADK), ProfileOptimizerPipeline (ADK)
- `src/infrastructure/a2a/` — A2A task receiver (input from jobflow-application)
- `src/infrastructure/llm/` — MCP client → jobflow-llm (question generation, answer frameworks)
- `src/infrastructure/postgres/` — outcome reads (for ProfileOptimizer)

## Agents

### InterviewPrepAgent
- **Receives:** A2A task ← `jobflow-application` (non-blocking, fire-and-forget)
  - Input: `{ job_description, company_context, tailored_resume, cover_letter }`
  - Output: `{ likely_questions[], answer_frameworks[], company_specific_tips[], prep_checklist[] }`
- Triggered after form submission — does not block application pipeline

### ProfileOptimizerAgent
- **Triggered:** Weekly Kubernetes CronJob
- Reads `application_outcomes` from Postgres (accepted/rejected patterns)
- Analyses which resume sections and skills correlate with success
- Output: `{ recommended_skills[], resume_section_improvements[], keyword_gaps[] }`
- Writes optimization report to Postgres; notified to user via jobflow-api

## Key rules
- InterviewPrepAgent is async — jobflow-application does NOT await its result
- ProfileOptimizerAgent runs as a Kubernetes CronJob (not KEDA scaled)
- KEDA scales InterviewPrepAgent on A2A task queue (min 0, max 3)
- See `.claude/architecture.md` for A2A agent card contract
