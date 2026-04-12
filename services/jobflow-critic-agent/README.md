# jobflow-critic-agent

A2A quality gate agent. Scores generated content (resume, cover letter) 0–10 and provides actionable feedback. Drives the Reflexion loop in jobflow-application.

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
- `src/domain/` — CritiqueResult entity, interfaces
- `src/application/` — CriticAgentPipeline (ADK)
- `src/infrastructure/a2a/` — A2A task receiver
- `src/infrastructure/llm/` — MCP client → jobflow-llm (scoring rubric evaluation)

## Protocols
- **Receives:** A2A task ← `jobflow-application`
  - Input: `{ content_type: resume|cover_letter, content, job_description, company_context }`
  - Output: `{ score: 0-10, passed: bool, feedback: string[] }`
- **Calls:** MCP → `jobflow-llm` (scoring rubric evaluation)

## Reflexion pattern
`score < 8` → jobflow-application regenerates with feedback → calls CriticAgent again.
Max 3 attempts per content type (resume, cover letter evaluated separately).

## Scoring dimensions
- Relevance to job description
- Personalisation (company context used)
- Tone appropriateness
- ATS keyword density
- Grammar and clarity

## Key rules
- Called twice per application: once for resume, once for cover letter
- KEDA scales on A2A task queue (min 0, max 5 — highest max, called most often)
- See `.claude/architecture.md` for A2A agent card contract
