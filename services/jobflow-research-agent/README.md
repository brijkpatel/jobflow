# jobflow-research-agent

A2A specialist agent. Gathers company intelligence before an application — culture, tech stack, recent news, hiring manager, red flags.

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
- `src/domain/` — CompanyIntel entity, interfaces
- `src/application/` — ResearchAgentPipeline (ADK)
- `src/infrastructure/a2a/` — A2A task receiver (input from jobflow-application)
- `src/infrastructure/mcp/` — MCP tool implementations: web_search, scrape_url, fetch_news

## Protocols
- **Receives:** A2A task ← `jobflow-application`
  - Input: `{ company_name, job_url, job_title }`
  - Output: `{ culture_notes, tech_stack, recent_news, hiring_manager?, red_flags[], glassdoor_rating }`
- **Calls:** MCP tools (self-hosted sidecar): `web_search` (Brave Search API), `scrape_url` (HTTPX + BeautifulSoup), `fetch_news`

## Key rules
- Stateless — no database, no Kafka
- Output feeds into cover letter personalisation and Q&A tone in jobflow-application
- KEDA scales on A2A task queue (min 0, max 3)
- See `.claude/architecture.md` for A2A agent card contract
