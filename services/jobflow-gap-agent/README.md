# jobflow-gap-agent

A2A specialist agent. Analyses skill and experience gaps between a job and a resume, produces an `apply_recommendation` (yes/no/maybe) to gate the application pipeline.

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
- `src/domain/` — GapAnalysis entity, interfaces
- `src/application/` — GapAgentPipeline (ADK)
- `src/infrastructure/a2a/` — A2A task receiver

## Protocols
- **Receives:** A2A task ← `jobflow-application`
  - Input: `{ job_requirements, user_resume, user_history }`
  - Output: `{ matched_skills[], gaps[], emphasis_areas[], dealbreakers[], apply_recommendation: yes|no|maybe, reasoning }`
- No outbound calls — pure reasoning against input data

## Key rules
- `apply_recommendation=no` → jobflow-application skips entire pipeline (avoids wasting LLM calls on poor fits)
- Stateless — no database, no Kafka
- KEDA scales on A2A task queue (min 0, max 3)
- See `.claude/architecture.md` for A2A agent card contract
