# Auto Job Application Platform — Architecture Plan

## Context
Building a multi-tenant auto job application platform — primarily for portfolio purposes, but designed to demonstrate real scalability patterns. Users upload resumes, set preferences (auto-apply or human-in-the-loop), and the platform crawls job boards, matches jobs to resumes using RAG + vector search, then applies via an agentic AI pipeline that tailors resumes, generates cover letters, answers screening questions, and submits applications.

**Portfolio goals demonstrated:**
- Event-driven microservices with Kafka (Redpanda)
- A2A + MCP — 2026 agentic AI standards (Linux Foundation)
- Google ADK for stateful agent orchestration
- RAG + vector search (Qdrant)
- Kubernetes auto-scaling (KEDA + HPA)
- Infrastructure as Code (Terraform + Oracle OKE)
- Observability (Prometheus + Grafana + Loki + LangFuse)
- Fine-tuned SLM (Gemma 3n E2B, QAT INT4, LiteRT-LM)

**Lean approach:** Each service has one clear reason to exist and one clear scaling characteristic. No speculative abstractions.

**Starting point:** City of Calgary careers site (simple HTML, no bot protection). Extend later via Playwright browser automation (LinkedIn, Indeed).

**Cloud:** Oracle Cloud Free Tier (4 ARM vCPUs + 24GB RAM + OKE managed K8s — $0). Fine-tuning: RunPod one-time ~$10. Ongoing cost: ~$1-2/mo (domain only — all LLM inference is local).

---

## Platform Name
Repos use prefix `jobflow-*` — confirm before creating.

---

## Service Architecture (renumbered, corrected)

### 1. `jobflow-web` — Next.js (TypeScript)
**Responsibility:** User-facing dashboard SPA.
- Resume upload + management
- Preference configuration (apply mode, salary, location, blacklists)
- Application history + status tracking
- HITL approval UI — review AI's tailored resume, cover letter, Q&A before approving
- Real-time updates via SSE from `jobflow-api`
- **Hosting:** Static export → OCI Object Storage + CDN (free)
- **No backend logic** — calls `jobflow-api` REST only

### 2. `jobflow-api` — Python + FastAPI
**Responsibility:** Public REST API. The only internet-facing backend service.
- Auth: JWT (python-jose + bcrypt) with users in Postgres — no third-party auth service
- User & organization CRUD
- Resume upload → gRPC to `resume-service` → returns parsed result
- Preferences CRUD
- Third-party credential management (encrypted store/retrieve)
- Application history & detail (see Application History API below)
- HITL approval endpoint → resumes A2A task via webhook
- SSE stream for real-time application status updates
- Pre-signed OCI Object Storage URL generation (tailored resume download)
- **gRPC client to:** `resume-service`
- **Scales:** HPA on RPS (min 2, max 10)

### 3. `resume-service` — Python + FastAPI
**Responsibility:** Resume CRUD, parsing, embedding.
- Wraps existing `resume-parser` library (NER/LLM/Regex extraction)
- Stores PDF to OCI Object Storage, URL in Postgres
- Chunks resume text → embeds with `all-MiniLM-L6-v2` → upserts to Qdrant `resume_chunks`
- Exposes gRPC server (called by `jobflow-api`)
- Exposes **MCP tool server** at `/mcp`: `fetch_user_resume(user_id, tenant_id)` → used by ApplicationAgent
- **Scales:** HPA on CPU (min 1, max 5)

### 4. `jobflow-crawler` — Python + HTTPX
**Responsibility:** Polls job boards, deduplicates, publishes to Kafka.
- Phase 1: HTTPX + BeautifulSoup (City of Calgary, simple HTML)
- Phase 2: Playwright browser automation (LinkedIn, Indeed)
- **Dedup strategy:**
  - Primary key: `SHA256(domain + job_id)` where `job_id` is extracted from URL params or page (e.g. `?jobId=12345`) — handles same job appearing at different URLs
  - Fallback: `SHA256(normalized_url)` when no job_id is found
  - Source of truth: Postgres `crawled_jobs` table (`dedup_key`, `last_seen`, `url`)
  - On each CronJob run: load active dedup keys into Redis for fast lookup; write-through on new discoveries
  - No TTL — job records persist indefinitely; re-crawled jobs update `last_seen` only
- **Scales:** K8s CronJob every 30 min, scale to 0 between runs

### 5. `jobflow-classifier` — Python + Google ADK
**Responsibility:** Consumes `raw-jobs`, enriches with AI, embeds, stores.
- ADK agent: calls `jobflow-llm` via **MCP** for title normalisation, skills, seniority, job type
- Embedding model: `all-MiniLM-L6-v2` (384-dim) — **must match `resume-service`** (same embedding space required for Qdrant similarity)
- Stores to Postgres `jobs` table + Qdrant `job_descriptions` collection
- Publishes enriched job to `classified-jobs` topic
- Exposes **MCP tool server** at `/mcp`: `fetch_job_details(job_id)` → used by ApplicationAgent
- **Scales:** KEDA on `raw-jobs` consumer lag (min 0, max 5)

### 6. `jobflow-matcher` — Python + FastAPI
**Responsibility:** Consumes `classified-jobs`, finds matching user resumes, publishes matches.
- Queries Qdrant `resume_chunks` with job embedding → top-K per user
- Weighted score: skill overlap (0.4) + semantic similarity (0.6)
- Filters by user preferences (min_score, location, salary_min, job_type, excluded_companies)
- Publishes to `match-results` topic
- **Scales:** KEDA on `classified-jobs` consumer lag (min 0, max 5)

### 7. `jobflow-application` — Python + Google ADK
**Responsibility:** Kafka consumer + orchestrator agent. Coordinates all specialist agents via A2A.
- Consumes `match-results`, starts one ADK pipeline per match
- **PARALLEL (A2A — simultaneous):**
  - A2A → `ResearchAgent`: company intel, culture, red flags
  - A2A → `GapAnalyzerAgent`: skill match, gaps, apply_recommendation
  - Merge results → ADK state; if `apply=no` → status=skipped, STOP
- **SEQUENTIAL with Reflexion (ADK state carries all context):**
  1. `tailor_resume(job + resume + gap_analysis)` via MCP → jobflow-llm
  2. A2A → `CriticAgent` → score < 8 → regenerate with feedback (max 3×)
  3. `cover_letter(job + tailored_resume + company_ctx)` via MCP → jobflow-llm
  4. A2A → `CriticAgent` → score < 8 → regenerate (max 3×)
  5. `qa_answers(job + resume + company_ctx)` via MCP → jobflow-llm
  6. `build_summary()` → fit score, gaps, confidence, what changed
- **HITL:** checkpoint to Redis → webhook → jobflow-api SSE → user approves/rejects
- **Post-submit (async):** A2A → `InterviewPrepAgent` (non-blocking)
- **HITL state:** ADK checkpoints to Redis after every step — pod-restart safe
- **Scales:** KEDA on `match-results` Kafka lag (min 0, max 5)

### 8. `jobflow-research-agent` — Python + Google ADK
**Responsibility:** Company intelligence gathering before application.
- Receives A2A task: `{ company_name, job_url, job_title }`
- Tools (MCP): `web_search`, `scrape_url`, `fetch_news`
- Output: `{ culture_notes, tech_stack, recent_news, hiring_manager?, red_flags[], glassdoor_rating }`
- Feeds into cover letter personalisation and Q&A tone
- **Scales:** KEDA on A2A task queue (min 0, max 3)

### 9. `jobflow-gap-agent` — Python + Google ADK
**Responsibility:** Skill and experience gap analysis + apply recommendation.
- Receives A2A task: `{ job_requirements, user_resume, user_history }`
- Compares job requirements against resume structured data
- Output: `{ matched_skills[], gaps[], emphasis_areas[], dealbreakers[], apply_recommendation: yes|no|maybe, reasoning }`
- `apply=no` → ApplicationAgent skips → avoids wasting LLM calls on poor fits
- **Scales:** KEDA on A2A task queue (min 0, max 3)

### 10. `jobflow-critic-agent` — Python + Google ADK
**Responsibility:** Quality gate — scores generated content and provides actionable feedback.
- Receives A2A task: `{ content_type: resume|cover_letter, content, job_description, company_context }`
- Scores on: relevance, personalisation, tone, ATS keyword density, grammar
- Output: `{ score: 0-10, passed: bool, feedback: string[] }`
- ApplicationAgent retries generation with feedback if `score < 8`, max 3 attempts
- **Pattern:** enables Reflexion loop — generate → critique → regenerate
- **Scales:** KEDA on A2A task queue (min 0, max 5 — called twice per application)

### 11. `jobflow-prep-agent` — Python + Google ADK
**Responsibility:** Two related post-application agents in one service.

**InterviewPrepAgent** (per-application, async, non-blocking):
- Triggered via A2A after successful submission
- Generates likely interview questions from job description + user background
- Generates suggested answers grounded in user resume
- Stores PDF → OCI Object Storage → publishes to `application-events{type=prep_ready}` Kafka

**ProfileOptimizerAgent** (weekly batch, CronJob):
- Analyses application outcomes across all users (submitted vs no-response vs rejected)
- Finds patterns in successful applications (which skills, roles, companies responded)
- Suggests resume improvements, preference tuning, skill gaps to address
- Writes optimisation report to Postgres `optimisation_reports` table
- Optionally auto-adjusts `user_preferences.min_match_score`
- Pattern: feedback loop / learning agent

- **Scales:** KEDA on A2A task queue (min 0, max 2)

### 12. `jobflow-llm` — Python + Google LiteRT-LM
**Responsibility:** Internal-only LLM inference service. Serves fine-tuned Gemma 3n E2B.
- Exposes **MCP tool endpoint** only: `generate(prompt, max_tokens, temperature) → text`
- All callers are ADK agents (classifier, application, research, gap, critic, prep) — all use MCP
- Model loaded from HuggingFace Hub on startup (`JOBFLOW_MODEL_VERSION` env var)
- **Internal only** — NetworkPolicy blocks all external traffic
- Now: LiteRT-LM (ARM-native, QAT INT4, <1.5GB RAM per pod)
- Later: NVIDIA Dynamo + TensorRT-LLM on GPU nodes — zero agent code changes
- **Scales:** KEDA on MCP request queue depth (min 1, max 8 within 24GB RAM budget)

### 13. `jobflow-notifier` — Go
**Responsibility:** Sends emails when HITL approval needed or application result arrives.
- Consumes: `application-events` Kafka topic (event_type filter)
- Integrates: Resend API
- **Scales:** KEDA on Kafka lag (min 0, max 2)

---

## Process Flow

### Full Pipeline

```
╔═════════════════════════════════════════════════════════════════════╗
║  CRAWL & CLASSIFY                                                   ║
║                                                                     ║
║  [K8s CronJob: 30min]                                               ║
║       │                                                             ║
║       ▼                                                             ║
║  jobflow-crawler ── dedup: Postgres crawled_jobs + Redis cache      ║
║       │           (SHA256(domain+job_id) or SHA256(normalized_url)) ║
║       │ Kafka: raw-jobs  ← lag = visible workload backlog           ║
║       ▼                                                             ║
║  jobflow-classifier  (ADK agent, scales on raw-jobs lag)            ║
║  ├─ MCP ──► jobflow-llm  (enrich: title, skills, seniority)        ║
║  ├─ embed: all-MiniLM-L6-v2 sidecar                                ║
║  └─ write: Postgres(jobs) + Qdrant(job_descriptions)                ║
║       │                                                             ║
║       │ Kafka: classified-jobs                                      ║
╚═══════╪═════════════════════════════════════════════════════════════╝
        │
╔═══════╪═════════════════════════════════════════════════════════════╗
║  MATCH│                                                             ║
║       ▼                                                             ║
║  jobflow-matcher                                                    ║
║  ├─ Qdrant: job_embedding → top-K resume chunks per user           ║
║  ├─ score = skill_overlap×0.4 + semantic_sim×0.6                   ║
║  ├─ filter: user_preferences                                        ║
║  └─ create: applications row (status=draft)                         ║
║       │                                                             ║
║       │ Kafka: match-results                                        ║
╚═══════╪═════════════════════════════════════════════════════════════╝
        │
╔═══════╪═════════════════════════════════════════════════════════════╗
║  APPLY│  (jobflow-application — Google ADK orchestrator)            ║
║       ▼                                                             ║
║  ADK State: { job, resume, company_ctx, gap_analysis,              ║
║               tailored_resume, cover_letter, qa, summary }          ║
║                                                                     ║
║  ┌─────────────────────────────────────────────────────────┐        ║
║  │  PHASE 1: PARALLEL (A2A — both fire simultaneously)     │        ║
║  │                                                          │        ║
║  │  A2A ──► ResearchAgent                                   │        ║
║  │          tools: web_search, scrape_url, fetch_news       │        ║
║  │          out: { culture, tech_stack, news, red_flags }   │        ║
║  │                                                          │        ║
║  │  A2A ──► GapAnalyzerAgent                                │        ║
║  │          out: { matched[], gaps[], emphasis[],           │        ║
║  │                 apply_recommendation: yes|no|maybe }     │        ║
║  │                                                          │        ║
║  │  merge both results → ADK state                          │        ║
║  │  if apply=no → status=skipped, STOP ✗                   │        ║
║  └─────────────────────────────────────────────────────────┘        ║
║                                                                     ║
║  ┌─────────────────────────────────────────────────────────┐        ║
║  │  PHASE 2: SEQUENTIAL with REFLEXION LOOPS               │        ║
║  │                                                          │        ║
║  │  MCP ──► jobflow-llm: tailor_resume                     │        ║
║  │  A2A ──► CriticAgent → score, feedback                  │        ║
║  │          score < 8? regenerate with feedback (max 3x)   │        ║
║  │                    ↻                                     │        ║
║  │  MCP ──► jobflow-llm: cover_letter                      │        ║
║  │          (uses company_ctx + gap_analysis in prompt)     │        ║
║  │  A2A ──► CriticAgent → score, feedback                  │        ║
║  │          score < 8? regenerate with feedback (max 3x)   │        ║
║  │                    ↻                                     │        ║
║  │  MCP ──► jobflow-llm: qa_answers                        │        ║
║  │  build_summary()                                         │        ║
║  └─────────────────────────────────────────────────────────┘        ║
║                                                                     ║
║  ┌─────────────────────────────────────────────────────────┐        ║
║  │  HITL (if apply_mode=hitl)                              │        ║
║  │  checkpoint → Redis                                      │        ║
║  │  REST ──► jobflow-api → SSE ──► jobflow-web             │        ║
║  │  user reviews: tailored resume, cover letter, Q&A       │        ║
║  │  user approves ──► REST ──► jobflow-api                 │        ║
║  │  ADK resumes from Redis checkpoint                       │        ║
║  └─────────────────────────────────────────────────────────┘        ║
║                                                                     ║
║  MCP ──► email_sender / form_filler: submit_application             ║
║  update Postgres → status=submitted                                 ║
║                                                                     ║
║  ┌─────────────────────────────────────────────────────────┐        ║
║  │  POST-SUBMIT (async, non-blocking)                      │        ║
║  │  A2A ──► InterviewPrepAgent                             │        ║
║  │          generates Q&A prep PDF → OCI Storage           │        ║
║  │          → Kafka: application-events{type=prep_ready}   │        ║
║  └─────────────────────────────────────────────────────────┘        ║
║       │                                                             ║
║       │ Kafka: application-events                                   ║
╚═══════╪═════════════════════════════════════════════════════════════╝
        │
╔═══════╪═════════════════════════════════════════════════════════════╗
║ NOTIFY│                                                             ║
║       ▼                                                             ║
║  jobflow-notifier  (consumes application-events, filters by type)   ║
║  ├─ submitted        → "Applied to {role} at {company}"             ║
║  ├─ pending_approval → "Please review — ready to apply"             ║
║  ├─ skipped          → "Skipped {role} — poor fit ({reason})"       ║
║  ├─ prep_ready       → "Interview prep ready for {role}"            ║
║  └─ failed           → "Application failed: {reason}"               ║
║       │                                                             ║
║       │ Resend API → user email                                     ║
╚═════════════════════════════════════════════════════════════════════╝

```

### API Layer (user-facing)

```
jobflow-web (Next.js — static CDN)
        │
        │  REST  (CRUD: upload resume, set prefs, list applications)
        │  SSE   (real-time: application status updates, HITL alerts)
        ▼
jobflow-api (FastAPI)
        │
        ├── gRPC ──────────────▶ resume-service
        │   (upload → parse → embed → return structured data)
        │
        ├── REST (webhook) ◀─── jobflow-application
        │   (HITL: "pending approval" notification)
        │
        └── SSE ──────────────▶ jobflow-web
            (push: status change events to open browser tabs)
```

---

## Protocol Decision Criteria

Use this to decide protocol for any new communication:

| Question | → Protocol |
|----------|-----------|
| Does the caller block and wait for a response? | → gRPC or REST |
| Is the caller a browser or external party? | → REST (browsers can't do native gRPC) |
| Is it internal service-to-service, typed, sync, high-frequency? | → **gRPC** |
| Can the consumer be slow? Should producer be decoupled? | → **Kafka** |
| Do you need replay, DLQ, or workload visibility (lag)? | → **Kafka** |
| Is one event consumed by multiple services? | → **Kafka** (fan-out via consumer groups) |
| Is the caller an ADK agent invoking a tool? | → **MCP** (framework-mandated) |
| Is it a streaming LLM response (token by token)? | → **gRPC** server-streaming or MCP/SSE |
| Is it a one-off webhook callback? | → **REST** |

### Protocol assignments (reviewed)

| Communication | Protocol | Criteria applied |
|--------------|----------|-----------------|
| crawler → classifier | **Kafka** | Decoupled, classifier is slow, lag = workload visibility |
| classifier → matcher | **Kafka** | Fan-out potential, consumer is slow (Qdrant queries) |
| matcher → application | **Kafka** | Consumer is very slow (LLM calls), must not block matcher |
| application → llm | **MCP** | ADK agent invoking a tool — protocol-mandated |
| classifier → llm | **MCP** | Classifier is an ADK agent — protocol-mandated |
| application → resume-service | **MCP** | ADK agent invoking a tool — protocol-mandated |
| application → classifier | **MCP** | ADK agent invoking a tool — fetch_job_details |
| jobflow-api → resume-service | **gRPC** | Sync, internal, user waits, typed contract |
| jobflow-api → browser | **REST + SSE** | Browser-facing; SSE for real-time push |
| jobflow-application → jobflow-api | **REST** | Webhook callback, one-off |
| application-events | **Kafka** | Consumed by notifier + any future audit consumers |

## Communication Protocol Map (summary)

---

## Kafka Topics (corrected — no separate submitter)

| Topic | Producer | Consumer(s) | Partitions | DLQ |
|-------|----------|-------------|------------|-----|
| `raw-jobs` | crawler | classifier | 4 | `raw-jobs.DLQ` |
| `classified-jobs` | classifier | matcher | 8 | `classified-jobs.DLQ` |
| `match-results` | matcher | orchestrator | 8 | `match-results.DLQ` |
| `application-events` | orchestrator | notifier, audit-log consumer | 4 | `application-events.DLQ` |

**DLQ policy:** Failed messages after 3 retries → DLQ topic. Grafana alert on DLQ lag > 0. Manual review + replay.

**Note:** Submission is handled inside `jobflow-application` via MCP tools — no separate Kafka topic or submitter service needed.

**Kafka:** Redpanda (single binary, Kafka-compatible, no ZooKeeper) — both local dev and production on OKE.

---

## Data Stores

### PostgreSQL (service-owned schemas)
| Schema | Owner | Key Tables |
|--------|-------|------------|
| `auth` | jobflow-api | users (password_hash, jwt_secret_version), organizations, memberships |
| `resumes` | resume-service | resumes, resume_versions |
| `jobs` | jobflow-classifier | jobs, job_sources |
| `applications` | jobflow-application | applications, application_events (append-only) |
| `preferences` | jobflow-api | user_preferences |

### Qdrant Collections
| Collection | Owner | Embedding model |
|------------|-------|----------------|
| `job_descriptions` | jobflow-classifier | `all-MiniLM-L6-v2` (384-dim) |
| `resume_chunks` | resume-service | `all-MiniLM-L6-v2` (384-dim) — **must match jobs** |

**Embedding consistency rule:** Both collections use identical model + version. Matcher queries `resume_chunks` using job embedding — different models = broken similarity. Lock via `EMBEDDING_MODEL_VERSION` env var shared across classifier + resume-service.

### Redis
| Namespace | Purpose |
|-----------|---------|
| `dedup:jobs:{dedup_key}` | Crawler dedup cache — loaded from Postgres `crawled_jobs` at run start; write-through on new jobs |
| `adk:checkpoint:{application_id}` | ApplicationAgent state checkpoint (HITL recovery) |
| `session:{token}` | Auth sessions |
| `ratelimit:submit:{user_id}` | Per-user submission rate limit |

### OCI Object Storage (free 10GB)
| Bucket | Contents |
|--------|---------|
| `resumes-raw` | User-uploaded PDFs/DOCX |
| `resumes-tailored` | AI-tailored resume PDFs (per application) |

---

## Key PostgreSQL Schemas

### `crawled_jobs` (crawler dedup — owned by jobflow-crawler)
```sql
id UUID PRIMARY KEY
dedup_key VARCHAR(64) UNIQUE NOT NULL  -- SHA256(domain+job_id) or SHA256(normalized_url)
url TEXT NOT NULL
domain VARCHAR(255)
external_job_id VARCHAR(255)           -- extracted from URL params or page, nullable
first_seen TIMESTAMPTZ DEFAULT now()
last_seen TIMESTAMPTZ DEFAULT now()    -- updated on re-crawl; no TTL/deletion
```

### `resumes`
```sql
id UUID PRIMARY KEY
user_id UUID REFERENCES users(id)
storage_url TEXT NOT NULL        -- OCI Object Storage URL for the raw PDF
file_name VARCHAR(255)
file_type VARCHAR(10)            -- 'pdf' | 'docx'
parsed_name VARCHAR(255)
parsed_email VARCHAR(255)
parsed_skills TEXT[]
qdrant_collection VARCHAR(100)   -- 'resume_chunks'
embedding_model_version VARCHAR(50)
created_at TIMESTAMPTZ DEFAULT now()
```

### `user_preferences`
```sql
id UUID PRIMARY KEY
user_id UUID REFERENCES users(id) UNIQUE
apply_mode VARCHAR(10) DEFAULT 'hitl'   -- 'hitl' | 'auto'
min_match_score FLOAT DEFAULT 0.65
salary_min INTEGER
location_preference VARCHAR(255)
preferred_job_types TEXT[]              -- ['full_time','contract']
excluded_companies TEXT[]
excluded_keywords TEXT[]
active BOOLEAN DEFAULT true
updated_at TIMESTAMPTZ DEFAULT now()
```

### `jobs`
```sql
id UUID PRIMARY KEY
source VARCHAR(50)
external_id VARCHAR(255)
url TEXT UNIQUE
title VARCHAR(255)
company VARCHAR(255)
location VARCHAR(255)
description TEXT
skills TEXT[]
seniority VARCHAR(50)
job_type VARCHAR(50)
salary_min INTEGER
salary_max INTEGER
closing_date DATE
qdrant_point_id UUID
embedding_model_version VARCHAR(50)
classified_at TIMESTAMPTZ
scraped_at TIMESTAMPTZ
created_at TIMESTAMPTZ DEFAULT now()
```

### `applications`
```sql
id UUID PRIMARY KEY
user_id UUID REFERENCES users(id)
resume_id UUID REFERENCES resumes(id)
job_id UUID REFERENCES jobs(id)
status VARCHAR(30)               -- 'draft'|'pending_approval'|'submitted'|'failed'|'rejected_by_user'
match_score FLOAT
tailored_resume_url TEXT         -- OCI Object Storage URL
cover_letter TEXT
qa_answers JSONB
ai_summary TEXT
apply_mode VARCHAR(10)
a2a_task_id VARCHAR(255)         -- A2A task reference for resume/tracking
submitted_at TIMESTAMPTZ
created_at TIMESTAMPTZ DEFAULT now()
```

### `user_credentials` (application-layer AES-256 encryption)
```sql
id UUID PRIMARY KEY
user_id UUID REFERENCES users(id)
credential_type VARCHAR(50)      -- 'city_of_calgary' | 'linkedin' | 'indeed'
portal_url TEXT                  -- the job portal URL this credential belongs to
username_enc BYTEA NOT NULL      -- AES-256 encrypted username
password_enc BYTEA NOT NULL      -- AES-256 encrypted password
created_at TIMESTAMPTZ DEFAULT now()
updated_at TIMESTAMPTZ DEFAULT now()
```

**Encryption approach — application-layer Fernet (AES-128-CBC + HMAC-SHA256):**
```python
# In jobflow-api at startup
from cryptography.fernet import Fernet

CRED_ENCRYPTION_KEY = os.environ["CRED_ENCRYPTION_KEY"]  # from OCI Vault via ESO
fernet = Fernet(CRED_ENCRYPTION_KEY)

# Store
username_enc = fernet.encrypt(username.encode())
password_enc = fernet.encrypt(password.encode())

# Retrieve
username = fernet.decrypt(username_enc).decode()
```

**Why application-layer over pgcrypto:**
- No Postgres extension required — works on self-hosted Postgres out of the box
- Key management via OCI Vault (already in infra plan) — encryption key never in DB
- Fernet provides authenticated encryption (encrypt + MAC) — tamper-evident
- Simple to rotate: re-encrypt all rows with new key, swap env var

**What is stored where:**
| Credential | Storage | Encryption |
|-----------|---------|------------|
| User platform login | Postgres `users` table | bcrypt + JWT (self-managed) |
| City of Calgary account | Postgres `user_credentials` | Fernet AES (app layer, key in OCI Vault) |
| LinkedIn / Indeed (Phase 2) | Postgres `user_credentials` | Fernet AES (same) |
| Infra secrets (DB pass, API keys) | OCI Vault → K8s Secrets via ESO | OCI-managed |

### `application_events` (append-only audit log)
```sql
id UUID PRIMARY KEY
application_id UUID REFERENCES applications(id)
event_type VARCHAR(50)   -- 'created'|'tailored'|'cover_letter_generated'|'pending_approval'|'approved'|'rejected_by_user'|'submitted'|'failed'
actor VARCHAR(20)        -- 'system' | 'user'
metadata JSONB
created_at TIMESTAMPTZ DEFAULT now()
```

---

## Agentic AI Design — A2A + MCP + Google ADK

### Protocol Standards (2026, Linux Foundation)

| Protocol | Role | Analogy |
|----------|------|---------|
| **A2A** (Agent2Agent) | Agent ↔ Agent — capability discovery via Agent Cards, task delegation | gRPC for agents |
| **MCP** (Model Context Protocol) | Agent ↔ Tool — standardised tool discovery and invocation | USB-C for tools |

### Architecture

```
Kafka: match-results
        │
        ▼
ApplicationAgent (jobflow-application) — ADK orchestrator
  ADK state: { application_id, job, user_resume,
               company_ctx, gap_analysis,
               tailored_resume, cover_letter,
               qa_answers, summary, apply_mode }
        │
        ├─ PHASE 1: PARALLEL (fire simultaneously)
        │   ├─ A2A ──▶ ResearchAgent (jobflow-research-agent)
        │   │           MCP tools: web_search, scrape_url, fetch_news
        │   │           out: { culture, tech_stack, news, red_flags }
        │   └─ A2A ──▶ GapAnalyzerAgent (jobflow-gap-agent)
        │               out: { matched[], gaps[], apply_recommendation }
        │   merge → ADK state; if apply=no → STOP (status=skipped)
        │
        ├─ PHASE 2: SEQUENTIAL with REFLEXION LOOPS
        │   ├─ MCP ──▶ jobflow-llm: tailor_resume
        │   │   A2A ──▶ CriticAgent (jobflow-critic-agent) → score/feedback
        │   │           score < 8? regenerate with feedback (max 3×) ↻
        │   ├─ MCP ──▶ jobflow-llm: cover_letter
        │   │   A2A ──▶ CriticAgent → score/feedback; max 3× ↻
        │   ├─ MCP ──▶ jobflow-llm: qa_answers
        │   └─ build_summary()
        │
        ├─ [if hitl] checkpoint to Redis ──▶ A2A: input-required
        │            REST ──▶ jobflow-api webhook ──▶ SSE ──▶ jobflow-web
        │            User approves ──▶ jobflow-api ──▶ A2A task resume
        │
        ├─ MCP ──▶ form_filler / email_sender: submit_application
        │
        └─ POST-SUBMIT (async, non-blocking)
            A2A ──▶ InterviewPrepAgent (jobflow-prep-agent)
                    generates PDF → OCI Storage → Kafka: application-events
```

### MCP Tool Servers (who hosts them)

| MCP Tool | Hosted By | Implementation |
|----------|-----------|---------------|
| `fetch_job_details(job_id)` | `jobflow-classifier` (owns jobs data) | Reads from Postgres |
| `fetch_user_resume(user_id, tenant_id)` | `resume-service` (owns resumes) | Reads from Postgres |
| `generate(prompt, ...)` | `jobflow-llm` | LiteRT-LM inference |
| `web_search(query)` | `jobflow-research-agent` (sidecar) | Brave Search API |
| `scrape_url(url)` | `jobflow-research-agent` (sidecar) | HTTPX + BeautifulSoup |
| `email_sender(to, subject, attachments)` | `jobflow-notifier` | Resend API |
| `form_filler(url, fields)` | `jobflow-application` (sidecar) | Playwright (Phase 2) |

Each service exposes its MCP tools at `/mcp` alongside its main API. ADK discovers tools at startup via MCP capability negotiation.

### HITL State Recovery

ADK checkpoint written to Redis `adk:checkpoint:{application_id}` after every pipeline step. If ApplicationAgent pod restarts mid-pipeline, on next A2A task delivery it reads checkpoint and resumes from last completed step. TTL: 7 days (covers approval timeout).

### LLM Backend

| | Now | Scale-up |
|-|-----|---------|
| Framework | Google **LiteRT-LM** (ARM-native) | NVIDIA **Dynamo** + TensorRT-LLM |
| Quantization | **QAT INT4** + TurboQuant (6x KV cache) | NVFP4/FP8 |
| Model | Fine-tuned **Gemma 3n E2B** (<1.5GB RAM) | Same model, multi-node |
| Model registry | **HuggingFace Hub** (public repo = portfolio) | Same |
| Version control | `JOBFLOW_MODEL_VERSION` env var | Same |

### LLM Observability: LangFuse (self-hosted)
Every `generate()` call traced: agent step → prompt → output → tokens → latency → cost.

---

## Credential Security Design

### Three credential tiers, clear separation

| Tier | What | Storage | Encryption |
|------|------|---------|------------|
| **Platform login** | User's jobflow account | Postgres `users` table | bcrypt (python-jose handles JWT) |
| **Third-party portal creds** | City of Calgary account, LinkedIn (Phase 2) | Postgres `user_credentials` | Fernet AES-256, key in OCI Vault |
| **Infra secrets** | DB password, API keys, Resend | OCI Vault → K8s Secrets via ESO | OCI KMS |

### Third-party credential flow
```
User enters City of Calgary credentials in jobflow-web
  → POST /users/me/credentials { type: "city_of_calgary", portal_url, username, password }
  → jobflow-api: fernet.encrypt(username), fernet.encrypt(password)
  → INSERT INTO user_credentials (username_enc, password_enc, ...)
  → Response: { id, credential_type } — plaintext never returned after this point

At apply time (Phase 2 — form submission):
  → ApplicationAgent MCP tool: fetch_portal_credentials(user_id, credential_type)
  → jobflow-api: SELECT + fernet.decrypt() in memory
  → Decrypted credentials passed to Playwright session
  → Never logged, never persisted beyond the session
```

### What is NEVER stored in plain text
- Platform passwords — Supabase Auth hashes with bcrypt
- Portal credentials — Fernet encrypted, key in OCI Vault
- API keys — OCI Vault only, synced to K8s Secrets by ESO, never in code or DB

---

## Application History API

### jobflow-api Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/applications` | Paginated list with status, job title, company, match score, date |
| GET | `/applications/{id}` | Full application detail (see below) |
| GET | `/applications/{id}/resume` | Pre-signed OCI URL for tailored resume PDF (15-min expiry) |
| GET | `/applications/{id}/events` | Audit trail of all state transitions |
| POST | `/applications/{id}/approve` | HITL approval — resumes A2A task |
| POST | `/applications/{id}/reject` | HITL rejection — cancels A2A task |

### Application Detail Response (`GET /applications/{id}`)
```json
{
  "id": "uuid",
  "status": "pending_approval",
  "created_at": "2026-04-09T10:00:00Z",
  "match_score": 0.82,
  "apply_mode": "hitl",

  "job": {
    "id": "uuid",
    "title": "Software Developer",
    "company": "City of Calgary",
    "location": "Calgary, AB",
    "url": "https://careers.calgary.ca/jobs/12345",
    "description": "...",
    "skills": ["Go", "Kubernetes", "Postgres"],
    "salary_min": 80000,
    "salary_max": 110000,
    "closing_date": "2026-04-30"
  },

  "resume": {
    "id": "uuid",
    "file_name": "john_doe_resume.pdf",
    "parsed_skills": ["Go", "Python", "Docker", "K8s"]
  },

  "ai_output": {
    "tailored_resume_url": "/applications/{id}/resume",  -- pre-signed, fetched on demand
    "cover_letter": "Dear Hiring Manager, ...",
    "qa_answers": [
      { "question": "Why do you want to work for the City?", "answer": "..." },
      { "question": "Describe your K8s experience", "answer": "..." }
    ],
    "summary": {
      "fit_score": 0.82,
      "matched_skills": ["Go", "Kubernetes"],
      "gaps": ["5+ years experience (you have 3)"],
      "ai_confidence": "high",
      "what_ai_did": "Reordered experience to emphasise K8s projects, added metrics to 2 bullet points, generated targeted cover letter referencing city infrastructure work"
    }
  },

  "events": [
    { "type": "created", "actor": "system", "at": "2026-04-09T10:00:00Z" },
    { "type": "tailored", "actor": "system", "at": "2026-04-09T10:00:05Z" },
    { "type": "pending_approval", "actor": "system", "at": "2026-04-09T10:00:12Z" }
  ]
}
```

### jobflow-web Application History UI

**List view:** Table with columns: Company, Role, Status badge, Match %, Date, Action button
- Status badges: Draft / Pending Your Approval / Submitted / Failed / Rejected by You
- Sortable by date, match score, status

**Detail view (per application):**
```
┌─────────────────────────────────────────────────┐
│ Software Developer — City of Calgary        0.82 │
│ Closing: Apr 30 · Calgary, AB              [Map] │
├──────────────────┬──────────────────────────────┤
│ JOB DESCRIPTION  │ AI SUMMARY                   │
│ [full text]      │ Matched: Go, Kubernetes       │
│                  │ Gaps: 5yr exp (you have 3)    │
│                  │ Confidence: High              │
├──────────────────┴──────────────────────────────┤
│ TAILORED RESUME          [Download PDF] [Diff ▼]│
│ (shows what changed vs original)                 │
├─────────────────────────────────────────────────┤
│ COVER LETTER                                     │
│ Dear Hiring Manager,                             │
│ [full text, copyable]                            │
├─────────────────────────────────────────────────┤
│ SCREENING Q&A                                    │
│ Q: Why City of Calgary?                          │
│ A: [AI answer, editable in HITL mode]            │
├─────────────────────────────────────────────────┤
│ TIMELINE                                         │
│ ✓ Matched   ✓ Tailored   ✓ Awaiting approval    │
├─────────────────────────────────────────────────┤
│          [Reject]          [Approve & Apply →]   │
└─────────────────────────────────────────────────┘
```

**HITL mode:** Cover letter and Q&A answers are **editable** before approval — user can tweak AI output before submitting.

---

## Fine-tuning Pipeline — `jobflow-training` repo

### Training Data Generation
```
1. Scrape 500+ real job postings (Calgary + Indeed sample)
2. Run Claude (API, ~$5) to generate:
   - Tailored resume variants per job
   - Cover letters (job + tailored resume → ideal cover letter)
   - Q&A pairs (common screening questions + ideal answers)
3. Format as Alpaca/Chat format JSONL
4. Push dataset to HuggingFace Hub (public)
```

### Fine-tuning
```
Base model: google/gemma-3n-E2B-it (instruction-tuned)
Framework:  Unsloth (2x faster, 60% less VRAM)
Method:     QLoRA (4-bit base + 16-bit LoRA adapters)
Hardware:   RunPod A10G x1, ~3-4 hours, ~$8-10 one-time
Tasks:      Multi-task: resume tailoring + cover letter + Q&A (one model, all 3)
```

### Export & Deploy
```
1. Merge LoRA adapters into base model
2. Export to GGUF Q4_K_M (llama.cpp compatible)
3. Convert to LiteRT-LM format for ARM inference
4. Push to HuggingFace Hub: brijkpatel/jobflow-gemma3n-e2b
5. jobflow-llm pod downloads on startup via JOBFLOW_MODEL_VERSION=v1.0
```

### Evaluation
- Held-out test set: 50 job-resume pairs
- Metrics: ROUGE-L (cover letter), human eval (resume quality), answer relevance (QA)
- Compare to: base Gemma 3n E2B (no fine-tuning) as baseline

---

## Infrastructure — Oracle OKE + Terraform

### Cloud: Oracle Always Free Tier
- **OKE** (Oracle Kubernetes Engine) — managed K8s, free
- **Compute:** 4 ARM Ampere A1 vCPUs + 24GB RAM — free
- **Object Storage:** 10GB — free
- **Networking:** 10TB outbound — free

### Terraform Modules (`jobflow-infra`)
```
modules/
  oke/              — OKE cluster, node pool (ARM A1), VPC
  object-storage/   — OCI buckets (resumes-raw, resumes-tailored)
  container-registry/ — OCIR (OCI Container Registry) for Docker images
  vault/            — OCI Vault for secrets
  dns/              — Domain + DNS records
  ingress/          — Nginx Ingress Controller + cert-manager (Let's Encrypt)
```

### Network Security (K8s NetworkPolicies)

| Service | External | Cluster-internal callers |
|---------|----------|------------------------|
| `jobflow-web` | OCI CDN only | — |
| `jobflow-api` | Internet (Ingress) | jobflow-web |
| `resume-service` | ❌ | jobflow-api (gRPC), jobflow-application (MCP) |
| `jobflow-llm` | ❌ | all ADK agents via MCP (classifier, application, research, gap, critic, prep) |
| `jobflow-application` | ❌ | Kafka consumer; outbound A2A to agent repos |
| `jobflow-research-agent` | ❌ | jobflow-application (A2A) only |
| `jobflow-gap-agent` | ❌ | jobflow-application (A2A) only |
| `jobflow-critic-agent` | ❌ | jobflow-application (A2A) only |
| `jobflow-prep-agent` | ❌ | jobflow-application (A2A) only |
| All others | ❌ | Kafka only |

### Ingress
- Nginx Ingress Controller (Helm)
- cert-manager + Let's Encrypt for TLS
- Routes: `api.jobflow.dev` → jobflow-api, `app.jobflow.dev` → OCI CDN (static)

### Secrets Management
- **External Secrets Operator** + **OCI Vault**
- Secrets defined in OCI Vault → ESO syncs to K8s Secrets automatically
- Secrets: DB password, JWT secret key, HuggingFace token, Resend API key, credential encryption key

### ARM64 CI/CD (GitHub Actions → OCIR → OKE)
```yaml
On PR:
  - lint + test (pytest / go test)
  - docker build --platform linux/arm64 (native, no emulation)

On merge to main:
  - docker build --push → OCIR
  - Helm upgrade --install in OKE
  - Smoke test (health endpoints)
```
**Runner:** Self-hosted GitHub Actions runner on one of the Oracle Ampere A1 ARM vCPUs — native ARM64 builds, no QEMU emulation needed. Register once, all service repos use it via `runs-on: self-hosted`.

### Auto-scaling Summary

| Service | Trigger | Min | Max |
|---------|---------|-----|-----|
| jobflow-web | OCI CDN | — | — |
| jobflow-api | HPA: CPU/RPS | 2 | 10 |
| resume-service | HPA: CPU | 1 | 5 |
| jobflow-crawler | CronJob (30 min) | 0 | 1 |
| jobflow-classifier | KEDA: `raw-jobs` lag | 0 | 5 |
| jobflow-matcher | KEDA: `classified-jobs` lag | 0 | 5 |
| jobflow-application | KEDA: `match-results` lag | 0 | 5 |
| jobflow-research-agent | KEDA: A2A task queue | 0 | 3 |
| jobflow-gap-agent | KEDA: A2A task queue | 0 | 3 |
| jobflow-critic-agent | KEDA: A2A task queue | 0 | 5 |
| jobflow-prep-agent | KEDA: A2A task queue (post-submit only) | 0 | 2 |
| jobflow-llm | KEDA: MCP request queue | 1 | 8 |
| jobflow-notifier | KEDA: `application-events` lag | 0 | 2 |

**Memory budget (Oracle 24GB):**
- System + K8s overhead: ~3GB
- Postgres + Redis + Qdrant + Redpanda: ~2GB
- All app services (small): ~3GB
- jobflow-llm × 4 pods: ~6GB (1.5GB each)
- Headroom: ~10GB — comfortable

---

## Observability Stack

| Tool | Purpose | Deployment |
|------|---------|------------|
| **Prometheus** | Metrics (infra + app) | kube-prometheus-stack Helm |
| **Grafana** | Dashboards | Same Helm chart |
| **Loki** | Log aggregation (structured JSON) | Helm |
| **Tempo** | Distributed tracing (OTel) | Helm |
| **LangFuse** | LLM traces, token cost, per-step latency | Self-hosted Helm |
| **OpenTelemetry** | Instrumentation SDK | Per-service |

**Key Grafana dashboards:**
- Jobs crawled/hour per source
- Kafka consumer lag per topic (with DLQ alert)
- Application pipeline funnel (matched → approved → submitted → success)
- LLM inference: tokens/sec, queue depth, cost/application
- KEDA scaling events

---

## Contracts — `contracts/` (monorepo)

> **Monorepo decision:** All services live in this single repo under `services/`. Contracts are in `contracts/` at the repo root — not a separate repo. This simplifies local development (one clone, one dev environment) and avoids cross-repo version coordination while still enforcing the same contract discipline.

- `contracts/proto/` — gRPC: resume-service ↔ jobflow-api
- `contracts/migrations/` — numbered SQL migrations (additive only)
- `contracts/kafka/schemas/` — JSON schemas for all Kafka topics + DLQs
- `contracts/mcp/` — MCP tool definitions (tool names, input/output schemas)
- `contracts/a2a/` — Agent Card definitions for all ADK agents
- `contracts/impact-map.json` — cross-service dependency map, updated on every contract change

---

## Monorepo Structure

```
jobflow/
  contracts/         ← shared schemas (proto, migrations, kafka, mcp, a2a)
  services/
    resume-service/  ← Python + FastAPI (gRPC server + MCP tool server)
    jobflow-api/     ← Python + FastAPI (public REST API)
    jobflow-crawler/ ← Python (CronJob scraper)
    jobflow-classifier/ ← Python + Google ADK
    jobflow-matcher/ ← Python + FastAPI
    jobflow-application/ ← Python + Google ADK (orchestrator)
    jobflow-research-agent/ ← Python + Google ADK
    jobflow-gap-agent/   ← Python + Google ADK
    jobflow-critic-agent/ ← Python + Google ADK
    jobflow-prep-agent/  ← Python + Google ADK
    jobflow-llm/     ← Python + LiteRT-LM
    jobflow-notifier/ ← Go
  web/               ← TypeScript + Next.js (user dashboard)
  training/          ← Python (Unsloth/TRL fine-tuning pipeline)
  infrastructure/    ← Terraform + Helm (OKE cluster + shared services)
  docs/plans/        ← architecture + implementation plans
```

Each service owns its `Dockerfile`, `charts/` (Helm), and `.github/workflows/` CI/CD. Merging a PR in `services/jobflow-matcher` triggers only that service's pipeline.

## Design decisions (changes from original plan)

| Decision | Original | Current | Reason |
|---|---|---|---|
| Contracts location | Separate `jobflow-contracts` repo | `contracts/` in monorepo | Simpler local dev, no cross-repo version pins |
| jobflow-classifier | Python + FastAPI, gRPC to llm | Python + Google ADK, MCP to llm | All LLM callers use the same ADK+MCP pattern — consistent, no two interface types on llm |
| jobflow-llm interfaces | gRPC (services) + MCP (agents) | MCP only | Classifier is now ADK — gRPC interface is unused |
| Auth | JWT + Supabase Auth | JWT + bcrypt + Postgres | No third-party auth dependency, simpler stack |

**Rule:** Terraform provisions what services share. Each service repo deploys itself.  
**Benefit:** Merging a PR in `jobflow-matcher` deploys only `jobflow-matcher` — no cross-repo coordination, no deployment bottleneck.

---

## Development Environment & AI Tooling

### Agent Workflow

| Agent | Use for | Cost |
|-------|---------|------|
| **Claude CLI** | Planning, architecture, cross-repo reasoning, security review | Limited tokens |
| **[claw-code](https://github.com/ultraworkers/claw-code)** | Daily implementation in terminal — Rust, fast, multi-provider | Free (Qwen OAuth / local) |
| **Zed + Qwen Code** | In-editor agentic editing | Free |

**claw-code** (179k stars, Rust) supports Qwen natively:
```bash
# Local via Ollama
OLLAMA_HOST=http://localhost:11434 claw --model qwen3-coder:14b
# Via DashScope API
DASHSCOPE_API_KEY=<key> claw --model qwen/qwen-max
```

**Qwen Code in Zed:** Settings → Add Agent → Install from Registry → Qwen Code

---

### Token Reduction: code-review-graph

**[tirth8205/code-review-graph](https://github.com/tirth8205/code-review-graph)** — 6.8x fewer tokens on reviews, 49x on daily tasks. Builds a persistent Tree-sitter knowledge graph; AI reads only relevant nodes instead of full files. Install per repo.

```bash
pip install code-review-graph
crg init   # builds graph for current repo
crg update # incremental update (SHA-256 tracked)
```

---

### Skills & MCP (install once, works in Claude CLI + claw-code)

**Install:** `git clone https://github.com/rohitg00/awesome-claude-code-toolkit ~/.claude/toolkit`

Key skills for this project:

| Skill/Agent | Purpose |
|-------------|---------|
| `api-documentation` | Auto-generate OpenAPI docs from FastAPI routes |
| `penetration-tester` | OWASP review of credential handling + API endpoints |
| `pytest-runner` | Test execution + coverage |
| `ui-design-review` | Accessibility + responsive design for jobflow-web |
| `/simplify` (built-in) | Refactor after implementation |
| `/plan` (built-in) | Architecture planning |

**MCP servers** (`~/.claude/settings.json`):
```json
{
  "mcpServers": {
    "github": { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"] },
    "postgres": { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-postgres"],
                  "env": { "POSTGRES_URL": "postgresql://localhost:5432/jobflow" } },
    "playwright": { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-playwright"] }
  }
}
```

---

### Code Structure — SOLID + Clean Architecture (all Python services)

Every service follows the same layered structure. Layers only depend inward.

```
src/
  domain/          # Pure Python — no framework imports
    models.py      # Entities, value objects (dataclasses)
    interfaces.py  # Protocols (IJobRepo, IEmbeddingService, ILLMService)
    exceptions.py  # Domain exceptions
  application/     # Use cases — orchestrates domain, no infra details
    use_cases.py   # e.g. ClassifyJobUseCase, TailorResumeUseCase
  infrastructure/  # Implements domain interfaces
    postgres/      # IJobRepo → PostgresJobRepo
    kafka/         # Producer, consumer
    qdrant/        # IVectorStore → QdrantVectorStore
    llm/           # ILLMService → LiteRTLMService
  api/             # FastAPI routes, Pydantic request/response models
    routes/
    schemas.py
  main.py          # Wires everything together (composition root)
tests/
  unit/            # Mock infra, test domain + use cases in isolation
  integration/     # Real infra (Docker), test full flow
```

**Key patterns applied:**

| Pattern | Where | Why |
|---------|-------|-----|
| Repository | `infrastructure/postgres/` | Decouple domain from DB |
| Strategy | `infrastructure/llm/` | Swap LiteRT-LM → Dynamo without changing use cases |
| Factory | `main.py` composition root | Wire concrete implementations to interfaces |
| Observer | Kafka consumers | React to events without coupling producers |
| Chain of Responsibility | resume-parser strategies (existing) | Fallback extraction |

**Interface example** (Python `Protocol` — structural typing, no inheritance needed):
```python
# domain/interfaces.py
from typing import Protocol
class ILLMService(Protocol):
    async def generate(self, prompt: str, max_tokens: int) -> str: ...

class IJobRepository(Protocol):
    async def get_by_id(self, job_id: UUID) -> Job: ...
    async def save(self, job: Job) -> None: ...
```

**Rule:** Use cases in `application/` depend only on `domain/interfaces.py` — never on `infrastructure/`. Tests mock at the interface boundary.

---

### CLAUDE.md — Modular & Concise

Keep CLAUDE.md ≤ 40 lines. Detailed context lives in `.claude/` subdocs, loaded on demand.

```
repo/
  CLAUDE.md              # ≤40 lines: purpose, run cmd, test cmd, key interfaces
  .claude/
    architecture.md      # Protocol contracts, dependencies, data owned
    patterns.md          # Design patterns in use, layer rules
    api.md               # Kafka topics / gRPC methods / MCP tools for this service
```

**CLAUDE.md template (concise):**
```markdown
# jobflow-<name>
<one sentence purpose>

## Run
\`\`\`bash
docker compose -f ../jobflow-infra/docker/docker-compose.dev.yml up -d
uv sync && uv run uvicorn src.main:app --reload
\`\`\`

## Test
\`\`\`bash
uv run pytest -m "not e2e"   # fast
uv run pytest                 # all
\`\`\`

## Structure
- `src/domain/` — pure Python, interfaces, entities
- `src/application/` — use cases
- `src/infrastructure/` — DB, Kafka, HTTP (implements domain interfaces)
- `src/api/` — FastAPI routes

## Key Rules
- Domain layer: zero framework imports
- Depend on interfaces, not implementations
- Secrets from env only
- See `.claude/architecture.md` for protocol contracts
```

---

## Build Order

### Phase 0 — Model (parallel, before any service needs it)
- `jobflow-training`: generate data → fine-tune → push to HuggingFace Hub

### Phase 1 — Foundation (local dev)
1. `jobflow-contracts` — all schemas, migrations, proto, MCP/A2A definitions
2. `jobflow-infra` — Docker Compose (Postgres, Redis, Qdrant, Redpanda, Redpanda Console)
3. `resume-service` — parse + embed resumes, gRPC server, MCP tool server
4. `jobflow-api` — auth, user, preferences, resume upload (gRPC client)
5. `jobflow-web` — upload UI, preferences, application history

### Phase 2 — Crawl & Classify
6. `jobflow-crawler` — Calgary scraper, Kafka producer
7. `jobflow-classifier` — consume raw-jobs, embed, publish classified-jobs

### Phase 3 — Match & Apply
8. `jobflow-matcher` — vector similarity, publish match-results
9. `jobflow-llm` — serve fine-tuned Gemma 3n via LiteRT-LM + dual interface (gRPC + MCP)
10. `jobflow-gap-agent` — skill gap analysis, apply_recommendation gating
11. `jobflow-research-agent` — company intel, web_search/scrape MCP tools
12. `jobflow-critic-agent` — Reflexion quality gate, scores resume + cover letter
13. `jobflow-application` — orchestrator agent, full pipeline: parallel Phase 1, Reflexion Phase 2, HITL

### Phase 4 — Notifications, Prep & Observability
14. `jobflow-prep-agent` — InterviewPrepAgent (async interview Q&A PDF)
15. `jobflow-notifier` — email for HITL + all event types (skipped, prep_ready, submitted, failed)
16. Grafana dashboards + LangFuse traces
17. HITL approval flow in `jobflow-web`

### Phase 5 — OKE Deployment
15. Terraform OKE cluster (Oracle free tier)
16. Helm charts per service
17. KEDA + HPA configuration
18. External Secrets Operator + OCI Vault
19. Nginx Ingress + TLS
20. GitHub Actions CI/CD (ARM64 buildx)

---

## Verification

- **Unit tests**: pytest (Python) — per service
- **Contract tests**: gRPC schema compatibility, MCP tool input/output validation
- **Integration test**: crawl 1 Calgary job → classify → match against test resume → agent produces tailored resume + cover letter
- **HITL test**: confirm A2A suspends at `input-required`, pod restart recovers from Redis checkpoint
- **E2E**: full pipeline → email notification with application draft to test account
- **Load test**: KEDA triggers correctly under simulated Kafka lag
- **LangFuse**: verify every agent step is traced with token cost

---

## Portfolio Story

### Scaling patterns (9 distinct mechanisms)
| Service | Pattern | Signal |
|---------|---------|--------|
| jobflow-crawler | CronJob, scale-to-0 | Scheduled batch, zero idle cost |
| jobflow-classifier | KEDA Kafka lag | Event-driven horizontal scale |
| jobflow-matcher | KEDA Kafka lag | Fan-out consumer, vector search |
| jobflow-application | KEDA Kafka lag | Consumer + orchestrator agent, Kafka-driven |
| jobflow-research/gap/critic/prep agents | KEDA A2A task queue | Fine-grained per-agent scaling |
| jobflow-llm | KEDA queue | ML inference scales independently |
| jobflow-api | HPA CPU/RPS | Standard stateless API tier |
| resume-service | HPA CPU | CPU-bound ML parsing |

### Technology choices (each communicates something specific)
| Tech | What it signals |
|------|----------------|
| **A2A Protocol** | 2026 agent interop standard (Linux Foundation, 150+ orgs) |
| **MCP** | Structured tool access — agents are composable |
| **Google ADK** | Purpose-built agentic framework, not hand-rolled loops |
| **Gemma 3n + QAT + LiteRT-LM** | ML engineering: training, quantization, edge serving |
| **LiteRT-LM → Dynamo** | Designed for scale-up, not MVP-only |
| **KEDA** | Intelligent auto-scaling beyond basic HPA |
| **Kafka DLQ** | Production-grade failure handling |
| **ADK checkpointing** | Stateful agent recovery — production-grade HITL |
| **External Secrets + OCI Vault** | Security-first, not K8s Secret base64 |
| **OpenTelemetry + LangFuse** | Distributed + LLM-specific observability |
| **Oracle OKE free tier** | Cost-conscious architecture decision |
| **Parallel A2A agents** | Research + Gap analysis fire simultaneously — reduces pipeline latency |
| **Reflexion loop (CriticAgent)** | Generate → score → regenerate — self-improving output quality |
| **Async post-submit agent** | InterviewPrepAgent fires-and-forgets — non-blocking UX |
