# System Architecture

## Services

| Service | Language | Scales on | Purpose |
|---|---|---|---|
| jobflow-web | Next.js | OCI CDN | User dashboard — upload, HITL, history |
| jobflow-api | Python + FastAPI | HPA RPS (2-10) | Public REST API, auth, SSE |
| resume-service | Python + gRPC + FastMCP | HPA CPU (1-5) | Parse, embed, store resumes |
| jobflow-crawler | Python | CronJob 30min | Scrape job boards, dedup, publish raw-jobs |
| jobflow-classifier | Python + ADK | KEDA raw-jobs lag (0-5) | Enrich + embed jobs via LLM |
| jobflow-matcher | Python + FastAPI | KEDA classified-jobs lag (0-5) | Vector match jobs to resumes |
| jobflow-application | Python + ADK | KEDA match-results lag (0-5) | Orchestrator — parallel agents + reflexion + HITL |
| jobflow-research-agent | Python + ADK | KEDA A2A queue (0-3) | Company intel via web search |
| jobflow-gap-agent | Python + ADK | KEDA A2A queue (0-3) | Skill gap + apply_recommendation |
| jobflow-critic-agent | Python + ADK | KEDA A2A queue (0-5) | Reflexion loop — score resume/cover letter |
| jobflow-prep-agent | Python + ADK | KEDA A2A queue (0-2) | Async interview prep PDF |
| jobflow-llm | Python + LiteRT-LM | KEDA MCP queue (1-8) | Fine-tuned Gemma 3n — MCP only |
| jobflow-notifier | Go | KEDA app-events lag (0-2) | Email via Resend |

## Protocols

| Communication | Protocol | Reason |
|---|---|---|
| Browser → backend | REST + SSE | Browser-facing |
| jobflow-api → resume-service | gRPC | Sync, internal, user waits |
| Any ADK agent → jobflow-llm | MCP | Agent tool invocation |
| crawler → classifier | Kafka | Async, decoupled, lag visibility |
| classifier → matcher | Kafka | Async, fan-out potential |
| matcher → application | Kafka | Consumer is slow (LLM calls) |
| application → specialist agents | A2A | Agent-to-agent delegation |
| application-events | Kafka | Consumed by notifier + future consumers |

## Kafka topics

| Topic | Producer | Consumers | DLQ |
|---|---|---|---|
| raw-jobs | crawler | classifier | raw-jobs.DLQ |
| classified-jobs | classifier | matcher | classified-jobs.DLQ |
| match-results | matcher | application | match-results.DLQ |
| application-events | application | notifier | application-events.DLQ |
| resume-parsed | resume-service | jobflow-matcher, jobflow-application (built in later tasks) | resume-parsed.DLQ |

## Data stores

| Store | Used by | Purpose |
|---|---|---|
| Postgres | all services (own schemas) | primary data |
| Qdrant | classifier, matcher, resume-service | vector search |
| Redis | crawler (dedup cache), application (ADK checkpoints) | cache + state |
| OCI Object Storage | resume-service, application | PDF storage |

## Auth
JWT (python-jose + bcrypt) — self-managed, users in Postgres. No third-party auth.

## LLM
Fine-tuned Gemma 3n E2B — QAT INT4, LiteRT-LM (ARM), <1.5GB/pod.
Model registry: HuggingFace Hub (`JOBFLOW_MODEL_VERSION` env var).
Scale-up path: NVIDIA Dynamo — zero agent code changes.

## Cloud
Oracle OKE free tier — 4 ARM vCPUs + 24GB RAM.
CI/CD: self-hosted GitHub Actions runner on Oracle Ampere A1 (native ARM64).
