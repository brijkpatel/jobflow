# jobflow-application

Kafka consumer + ADK orchestrator agent. Consumes `match-results`, runs the full application pipeline (parallel research + gap analysis, Reflexion content generation, HITL checkpoint, form submission), and coordinates all specialist agents via A2A.

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
- `src/domain/` — Application entity, ADK state schema, interfaces
- `src/application/` — ApplicationPipeline (ADK orchestrator)
- `src/infrastructure/kafka/` — Kafka consumer (match-results)
- `src/infrastructure/redis/` — ADK checkpoint store (`adk:checkpoint:{application_id}`)
- `src/infrastructure/a2a/` — A2A clients for specialist agents
- `src/infrastructure/llm/` — MCP client → jobflow-llm (tailor_resume, cover_letter, qa_answers)
- `src/api/` — REST webhook receiver (HITL approval/rejection from jobflow-api)

## Pipeline
```
consume match-results
  → PARALLEL A2A: ResearchAgent + GapAnalyzerAgent
  → if apply=no: status=skipped, STOP
  → tailor_resume (MCP → llm) → CriticAgent (A2A) → retry max 3×
  → cover_letter (MCP → llm) → CriticAgent (A2A) → retry max 3×
  → qa_answers (MCP → llm)
  → build_summary()
  → [if hitl] checkpoint Redis → webhook → jobflow-api → SSE → user
  → form_filler / email_sender (MCP)
  → A2A → InterviewPrepAgent (async, non-blocking)
  → publish application-events
```

## Protocols
- **Consumes:** Kafka `match-results`
- **Publishes:** Kafka `application-events`
- **Calls:** A2A → `jobflow-research-agent`, `jobflow-gap-agent`, `jobflow-critic-agent`, `jobflow-prep-agent`
- **Calls:** MCP → `jobflow-llm` (generate), `resume-service` (fetch_user_resume), `jobflow-classifier` (fetch_job_details)
- **Calls:** REST webhook → `jobflow-api` (HITL notification)
- **Receives:** REST ← `jobflow-api` (HITL approval/rejection)

## HITL state recovery
ADK checkpoints to Redis `adk:checkpoint:{application_id}` after every step.
Pod restart → reads checkpoint → resumes from last completed step.
TTL: 7 days (covers approval timeout window).

## Key rules
- One ADK pipeline per match — never process two simultaneously for same user+job
- KEDA scales on `match-results` consumer lag (min 0, max 5)
- See `.claude/architecture.md` for A2A agent card contracts
