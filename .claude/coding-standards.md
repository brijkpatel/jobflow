# Coding Standards

## Decoupling (pragmatic — scale to complexity)

```
Simple feature, no extension expected   → plain function or class
Multi-step workflow / branching logic   → service or orchestrator
Needs to be testable / mockable         → Protocol + concrete implementation
Tech that might be swapped later        → interface + provider/client implementation
Complex construction / wiring           → factory or composition helper
```

**One non-negotiable rule regardless of pattern:**
Business-logic modules (`service.py`, `orchestrator.py`, pure helpers, decision code) never import FastAPI, ADK, Kafka, SQLAlchemy, or other framework-heavy concrete implementations directly. Swapping a tech should mostly mean changing wiring plus the concrete class that talks to that tech, not rewriting the workflow logic.

## Suggested service structure (adapt to complexity)

```
src/
  models.py        # entities, value objects, shared types
  interfaces.py    # Protocols / abstract contracts
  services/        # business logic units
  orchestrators/   # multi-step flows, agent coordination, pipelines
  providers/       # concrete integrations: DB, queue, LLM, storage, ADK
  factories.py     # optional wiring helpers for complex setup
  api/             # FastAPI routes / HTTP schemas
    routes/
    schemas.py
  main.py          # composition root — wires interfaces to implementations
tests/
  unit/            # mock at interface boundary
  integration/     # real providers via Docker / test containers
```

Not every service needs every folder. Prefer the smallest structure that keeps business logic separate from transport and infrastructure concerns.

## Interfaces

Use Python `Protocol` (structural typing — no inheritance needed):

```python
from typing import Protocol
from uuid import UUID

class IJobRepository(Protocol):
    async def get_by_id(self, job_id: UUID) -> Job | None: ...
    async def save(self, job: Job) -> None: ...
```

## Boundary discipline

- No framework models in service/orchestrator signatures
- Map HTTP payloads, Kafka events, ORM rows, and ADK/tool payloads at the boundary before business logic sees them
- No direct env/config reads outside `main.py`, factories, or explicit wiring modules
- Time, UUID generation, retry policy, and similar workflow-affecting concerns should be injectable when they influence decisions
- External side effects (LLM, DB, queue, email, storage, search, auth) stay behind Protocols or explicit interfaces
- Keep transaction ownership explicit: define where write units start/end instead of letting persistence details leak through the call stack

## Rules

- Max 200 lines per file — split if exceeded
- Type hints on all public functions
- No bare `except:` — catch specific exceptions
- Docstrings only on Protocol methods — 1 line max
- No inline comments unless logic is non-obvious math or algorithm
- No speculative abstractions — build for what the task requires
- No backwards-compatibility shims — change the code directly
- `main.py` and explicit factory modules are where business logic is wired to concrete implementations
- Keep FastAPI routes, ADK setup, DB clients, and Kafka clients out of business-logic modules
- Reads should not mutate state; commands should not also behave like queries

## Go (notifier service)

- Interfaces defined in consumer package, not provider
- No `init()` functions
- Standard Go project layout

## Design patterns (apply where they fit, not everywhere)

| Pattern | Apply when |
|---|---|
| Repository | Separating domain from DB queries |
| Strategy | Swappable algorithms or tech (LLM backend, embedding model) |
| Factory | Composition root wiring |
| Observer | Kafka consumer event handling |
| Chain of Responsibility | Fallback extraction pipelines |
