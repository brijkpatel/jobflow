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
node scripts/forge.js status
# or via Claude Code skill: /forge
```
If a task is in progress, resume from `last_completed` — do not redo completed steps.
To hand off to local LLM: `node scripts/forge.js next` or `/forge next`

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

<!-- code-review-graph MCP tools -->
## MCP Tools: code-review-graph

**IMPORTANT: This project has a knowledge graph. ALWAYS use the
code-review-graph MCP tools BEFORE using Grep/Glob/Read to explore
the codebase.** The graph is faster, cheaper (fewer tokens), and gives
you structural context (callers, dependents, test coverage) that file
scanning cannot.

### When to use graph tools FIRST

- **Exploring code**: `semantic_search_nodes` or `query_graph` instead of Grep
- **Understanding impact**: `get_impact_radius` instead of manually tracing imports
- **Code review**: `detect_changes` + `get_review_context` instead of reading entire files
- **Finding relationships**: `query_graph` with callers_of/callees_of/imports_of/tests_for
- **Architecture questions**: `get_architecture_overview` + `list_communities`

Fall back to Grep/Glob/Read **only** when the graph doesn't cover what you need.

### Key Tools

| Tool | Use when |
|------|----------|
| `detect_changes` | Reviewing code changes — gives risk-scored analysis |
| `get_review_context` | Need source snippets for review — token-efficient |
| `get_impact_radius` | Understanding blast radius of a change |
| `get_affected_flows` | Finding which execution paths are impacted |
| `query_graph` | Tracing callers, callees, imports, tests, dependencies |
| `semantic_search_nodes` | Finding functions/classes by name or keyword |
| `get_architecture_overview` | Understanding high-level codebase structure |
| `refactor_tool` | Planning renames, finding dead code |

### Workflow

1. The graph auto-updates on file changes (via hooks).
2. Use `detect_changes` for code review.
3. Use `get_affected_flows` to understand impact.
4. Use `query_graph` pattern="tests_for" to check coverage.

## graphify

This project has a graphify knowledge graph at graphify-out/.

Rules:
- Before answering architecture or codebase questions, read graphify-out/GRAPH_REPORT.md for god nodes and community structure
- If graphify-out/wiki/index.md exists, navigate it instead of reading raw files
- After modifying code files in this session, run `python3 -c "from graphify.watch import _rebuild_code; from pathlib import Path; _rebuild_code(Path('.'))"` to keep the graph current
