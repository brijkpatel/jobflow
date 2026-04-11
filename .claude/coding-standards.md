# Coding Standards

## Decoupling (pragmatic — scale to complexity)

```
Simple feature, no extension expected   → plain class
Needs to be testable / mockable         → class + interface (Protocol)
Tech that might be swapped later        → interface + adapter
Core domain boundary (LLM, DB, queue)  → port + adapter (hexagonal)
```

**One non-negotiable rule regardless of pattern:**
`domain/` and `application/` layers never import from `infrastructure/`, ADK, FastAPI, Kafka, SQLAlchemy, or any framework. Swapping a tech = change one adapter, nothing else.

## Layer structure (Python services)

```
src/
  domain/          # pure Python — no framework imports
    models.py      # entities, value objects (dataclasses)
    interfaces.py  # Protocols — IJobRepo, ILLMService, IEmailSender
    exceptions.py  # domain exceptions
  application/     # use cases — orchestrates domain, no infra details
    use_cases.py
  infrastructure/  # implements domain interfaces
    postgres/
    kafka/
    qdrant/
    llm/
    adk/           # ADK Agent instantiation lives here
  api/             # FastAPI routes — thin adapters only
    routes/
    schemas.py
  main.py          # composition root — wires interfaces to implementations
tests/
  unit/            # mock at interface boundary
  integration/     # real infra via Docker
```

## Interfaces

Use Python `Protocol` (structural typing — no inheritance needed):

```python
from typing import Protocol
from uuid import UUID

class IJobRepository(Protocol):
    async def get_by_id(self, job_id: UUID) -> Job | None: ...
    async def save(self, job: Job) -> None: ...
```

## Rules

- Max 200 lines per file — split if exceeded
- Type hints on all public functions
- No bare `except:` — catch specific exceptions
- Docstrings only on Protocol methods — 1 line max
- No inline comments unless logic is non-obvious math or algorithm
- No speculative abstractions — build for what the task requires
- No backwards-compatibility shims — change the code directly
- `main.py` is the only place that imports from both `domain/` and `infrastructure/`

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
