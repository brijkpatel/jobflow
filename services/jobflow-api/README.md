# jobflow-api

Public REST API — the only internet-facing backend service. Handles auth, user management, resume upload, preferences, HITL approval, and SSE streams.

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
- `src/domain/` — entities, interfaces (Protocol), exceptions — no framework imports
- `src/application/` — use cases (UploadResumeUseCase, HITLApprovalUseCase, ...)
- `src/infrastructure/` — Postgres, gRPC client (resume-service), OCI Storage, A2A webhook
- `src/api/` — FastAPI routes, Pydantic schemas, SSE endpoints

## Protocols
- **Exposes:** REST (public, internet-facing via Nginx Ingress)
- **Exposes:** SSE stream `/sse/applications` → real-time status to jobflow-web
- **Calls:** gRPC → `resume-service:50051` (ParseResume, GetResume)
- **Receives:** REST webhook ← `jobflow-application` (HITL pending_approval notification)

## Key rules
- Only service with external ingress — all others are cluster-internal
- JWT auth on all routes (python-jose + bcrypt, users in Postgres)
- Credential encryption: Fernet AES-256, key from OCI Vault via ESO
- Never return decrypted portal credentials in API responses
- See `.claude/architecture.md` for full protocol contracts
