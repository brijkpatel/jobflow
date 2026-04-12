# Jobflow — Implementation Plan

## Status: Pre-implementation (architecture complete, nothing built)

All design decisions are locked in `system-architecture.md`. This plan covers build order and dependencies.

---

## Build Order

### Phase 1 — Contracts (foundation, everything else depends on these)

All contracts must be finalized before services are written. Services are consumers of contracts.

| Task | Artifacts |
|------|-----------|
| SQL migrations | `contracts/migrations/` — all schemas: auth, resumes, jobs, applications, preferences, credentials, crawled_jobs, application_events |
| Kafka schemas | `contracts/kafka/schemas/` — raw-jobs, classified-jobs, match-results, application-events (+ DLQ variants) |
| gRPC proto | `contracts/proto/resume.proto` — ResumeService: ParseResume, GetResume |
| MCP tool definitions | `contracts/mcp/tools/` — generate, fetch-job-details, fetch-user-resume, web-search, email-sender |
| A2A agent cards | `contracts/a2a/cards/` — research-agent, gap-agent, critic-agent, prep-agent |

### Phase 2 — LLM + Model (unblocked, no service deps)

Fine-tune the Gemma 3n model before services that call it are built.

| Task | Notes |
|------|-------|
| Training data generation | Scrape ~500 jobs, call Claude API to generate tailored resumes, cover letters, Q&A pairs |
| Fine-tune Gemma 3n E2B | Unsloth + QLoRA on RunPod A10G, ~$10 |
| Export + convert to LiteRT-LM | Merge LoRA, GGUF Q4_K_M, LiteRT-LM ARM format |
| Push to HuggingFace Hub | `brijkpatel/jobflow-gemma3n-e2b` |

### Phase 3 — Core Services (strict dependency order)

```
jobflow-llm         ← no service deps (needs model from Phase 2)
resume-service      ← needs migrations, proto
jobflow-api         ← needs resume-service (gRPC), migrations
jobflow-web         ← needs jobflow-api (REST)
jobflow-crawler     ← needs migrations (crawled_jobs), Kafka schemas
jobflow-classifier  ← needs jobflow-llm (MCP), Kafka raw-jobs schema, migrations (jobs)
jobflow-matcher     ← needs Kafka classified-jobs, Qdrant
```

### Phase 4 — Agent Services (depend on A2A cards + jobflow-llm)

```
jobflow-research-agent  ← needs A2A card, web-search MCP tool
jobflow-gap-agent       ← needs A2A card
jobflow-critic-agent    ← needs A2A card
jobflow-prep-agent      ← needs A2A card
jobflow-application     ← needs all 4 agents (A2A), jobflow-llm (MCP), Kafka match-results
jobflow-notifier        ← needs Kafka application-events, email-sender MCP
```

### Phase 5 — Infrastructure

| Task | Notes |
|------|-------|
| Terraform: OKE cluster | OCI Free Tier ARM A1, managed K8s |
| Terraform: shared services | Postgres, Redis, Qdrant, Redpanda on OKE |
| Terraform: OCI resources | Object Storage buckets, Vault, Container Registry, DNS |
| Helm charts per service | Deployment, Service, HPA/KEDA ScaledObject, NetworkPolicy per service |
| Observability stack | kube-prometheus-stack, Loki, Tempo, LangFuse Helm installs |
| CI/CD pipelines | GitHub Actions: lint+test on PR, build+push+deploy on merge to main |
| Self-hosted runner setup | ARM64 runner on Oracle A1 node |

### Phase 6 — Testing + Validation

| Task | Notes |
|------|-------|
| Integration tests | Full pipeline: crawl → classify → match → apply (mocked LLM) |
| E2E smoke test | Health endpoint checks + single job through pipeline on staging |
| HITL flow test | Verify Redis checkpoint, webhook, SSE, approve/reject flow |
| Load test | k6: 100 concurrent applications, verify KEDA auto-scaling |

---

## Critical path

```
contracts → jobflow-llm + training → resume-service + jobflow-classifier
         → jobflow-api → jobflow-web
         → jobflow-crawler → jobflow-classifier → jobflow-matcher
         → specialist agents → jobflow-application
         → jobflow-notifier
         → infra → deploy → smoke test
```

## Key constraints

- `EMBEDDING_MODEL_VERSION` env var must be identical in `resume-service` and `jobflow-classifier` — both use `all-MiniLM-L6-v2` (384-dim). Qdrant similarity breaks if they differ.
- `jobflow-llm` must be running before any ADK agent service starts — all use it via MCP.
- Contracts cannot change once a consuming service is implemented without architect review + impact-map.json update.
- All Docker images: `--platform linux/arm64` (Oracle Ampere A1 target).
