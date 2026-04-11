# jobflow
Multi-tenant auto job application platform. Crawls job boards, matches jobs to resumes via RAG, applies via agentic AI pipeline.

## Structure
```
contracts/     proto, Kafka schemas, SQL migrations, MCP tools, A2A cards
services/      each microservice (Python + ADK, except notifier in Go)
web/           Next.js dashboard
infrastructure/ Terraform (Oracle OKE) + Helm charts
training/      Gemma 3n fine-tuning pipeline
docs/plans/    L1 system plan + L2 per-service designs
```

## Session start
Run this before anything else:
```bash
python scripts/task.py status
```
If a task is in progress, resume from `last_completed` — do not redo completed steps.
To hand off to local LLM: `python scripts/task.py next`

## Key rules
- Domain layer: zero framework imports
- Depend on interfaces (Protocol), not implementations
- Contracts change = architect agent review required + impact-map.json updated
- See `.claude/coding-standards.md` for code standards
- See `.claude/workflow.md` for development process
- See `.claude/architecture.md` for system design
- See `.claude/agents/` for review agents

## Impact analysis
```bash
python scripts/impact-analysis.py --from-git-diff   # affected services from current diff
python scripts/gen-impact-map.py                     # regenerate impact-map after adding services
```
