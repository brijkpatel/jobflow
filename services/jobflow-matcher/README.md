# jobflow-matcher

Consumes `classified-jobs`, queries Qdrant for matching resume chunks per user, applies preference filters, and publishes match-results to Kafka.

## Run
```bash
docker compose -f ../../infrastructure/docker/docker-compose.dev.yml up -d
uv sync && uv run uvicorn src.main:app --reload
```

## Test
```bash
uv run pytest -m "not integration"
uv run pytest
```

## Structure
- `src/domain/` — Match entity, interfaces (VectorStore, PreferenceRepository, MatchPublisher)
- `src/application/` — MatchJobsUseCase
- `src/infrastructure/kafka/` — Kafka consumer (classified-jobs) + producer (match-results)
- `src/infrastructure/qdrant/` — Qdrant query client (resume_chunks collection)
- `src/infrastructure/postgres/` — user_preferences reads, applications writes

## Protocols
- **Consumes:** Kafka `classified-jobs`
- **Publishes:** Kafka `match-results`
- **Reads:** Qdrant `resume_chunks` (queries with job embedding, top-K per user)
- **Reads:** Postgres `user_preferences` (filter by min_score, location, salary, excluded_companies)
- **Writes:** Postgres `applications` row (status=draft)

## Scoring
`score = skill_overlap × 0.4 + semantic_similarity × 0.6`

Filters applied after scoring:
- `min_match_score` — drop below threshold
- `location_preference` — location match required
- `salary_min` — job salary_max must exceed user minimum
- `excluded_companies` — skip blacklisted companies
- `excluded_keywords` — skip jobs containing banned terms

## Key rules
- Does NOT write to Qdrant — reads only
- Creates `applications` row on match (status=draft)
- KEDA scales on `classified-jobs` consumer lag (min 0, max 5)
- See `.claude/architecture.md` for Kafka schemas
