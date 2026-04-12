# jobflow-crawler

Polls job boards, deduplicates, and publishes raw jobs to Kafka. Runs as a K8s CronJob every 30 minutes, scales to 0 between runs.

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
- `src/domain/` — Job entity, interfaces (JobBoardScraper, DeduplicationStore, JobPublisher)
- `src/application/` — CrawlJobsUseCase
- `src/infrastructure/http/` — HTTPX + BeautifulSoup scrapers (Phase 1), Playwright (Phase 2)
- `src/infrastructure/kafka/` — Kafka producer (raw-jobs topic)
- `src/infrastructure/redis/` — Redis dedup cache
- `src/infrastructure/postgres/` — crawled_jobs table (source of truth for dedup)

## Protocols
- **Publishes:** Kafka `raw-jobs` topic
- **Reads:** Redis cache (dedup fast-path) + Postgres `crawled_jobs` (source of truth)
- **No inbound calls** — runs as CronJob

## Dedup strategy
- Primary key: `SHA256(domain + job_id)` extracted from URL params
- Fallback: `SHA256(normalized_url)` when no job_id found
- Postgres `crawled_jobs` is the source of truth (no TTL — persists forever)
- Redis cache loaded at CronJob start for fast in-memory lookup; write-through on new discoveries

## Key rules
- Phase 1: HTTPX + BeautifulSoup (City of Calgary only)
- Phase 2: Playwright for LinkedIn/Indeed (requires browser automation)
- Never publish duplicate jobs — dedup before Kafka publish
- See `.claude/architecture.md` for scraper interfaces
