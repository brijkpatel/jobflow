---
name: tasks
description: Manage the task queue in tasks/queue.json. Auto-extract subtasks from plans, pick ready tasks, handle dependencies. Invoke at session start and after each workflow step.
---

# Task Queue Management

Queue file: `tasks/queue.json`

Steps in order: `plan_written` → `plan_approved` → `implemented` → `regression` → `compliance` → `developer` → `qa` → `specialist` → `user_review` → `merged`

Step descriptions:
- `plan_written`  — L3 task plan written (writing-plans skill)
- `plan_approved` — Plan approved by compliance agent
- `implemented`   — Implementer subagent done (TDD, all tests pass)
- `regression`    — Regression agent passed (blast radius + affected test suites)
- `compliance`    — Compliance agent passed (diff matches plan)
- `developer`     — Developer agent passed (code quality + SOLID)
- `qa`            — QA agent passed (test coverage + correctness)
- `specialist`    — Role-specific agent passed (if declared in task plan)
- `user_review`   — User reviewed and approved (always a manual checkpoint)
- `merged`        — Squash merged to main, branch deleted, main pushed

---

## `/task` or `/task status`

Read `tasks/queue.json`. Display:
- Current task: description, branch, plan file, steps, and subtasks
- Next step with description
- If no current task: shows next ready task and full queue with dependency status

If no current task and no ready tasks: shows blocked tasks + what they depend on.

## `/task start <description>`

1. Read current git branch
2. Create initial task with unique id (YYYYMMDDHHMMSSsss)
3. Add to `current` in queue.json
4. Auto-detect plan file under `services/<service>/docs/plans/` or `docs/plans/`
5. `git commit -m "task: start — <description>"`
6. Show next step: `plan_written`

## `/task done <step>`

Mark a step complete, then automatically invoke the next agent (see **Agent auto-chain** below).

1. Run `node scripts/task.js done <step>`
2. Follow the auto-chain routing table — invoke the next agent, gather context first
3. If agent returns APPROVED: run `node scripts/task.js done <next-step>` and continue chain
4. If agent returns BLOCKED: stop, report issues to user, do NOT mark next step done
5. Pause at `user_review` — always wait for explicit user confirmation before marking done

## Specialist auto-detection

Before running any review chain, detect which specialist agents are needed.
Do this twice: once at **plan review** (from task description + plan content), once at **implementation review** (from changed file paths).
Never require the user to declare specialists manually — infer from signals.

### Detection signals

| Specialist | Triggers on (description / plan keywords) | Triggers on (changed file paths) |
|---|---|---|
| `architect` | new service, service boundary, Kafka schema, proto change, contract, cross-service, migration, new topic, A2A card | `contracts/`, `*.proto`, `*schema*`, `*migration*`, `infrastructure/`, `services/*/contracts/` |
| `ml-developer` | LLM, embedding, inference, fine-tuning, RAG, vector, Gemma, model, classifier, ranker, retrieval | `training/`, `*embed*`, `*infer*`, `*llm*`, `*model*`, `*rag*`, `*vector*`, `*classifier*` |
| `a2a-specialist` | A2A, ADK, agent, MCP tool, orchestration, subagent, AgentCard, dispatch | `*agent*`, `*a2a*`, `*mcp*`, `*adk*`, `contracts/mcp-tools/`, `*orchestrat*` |
| `api-security` | auth, JWT, token, OAuth, secret, credential, encryption, API key, public endpoint, permission | `*auth*`, `*security*`, `*token*`, `*oauth*`, `*credential*`, `src/api/`, `*middleware*` |

### How to detect

**At plan review** (`plan_written` just marked done):
1. Read task description from `tasks/queue.json current.description`
2. Read plan file contents
3. Match keywords from the table above against both
4. Collect all matched specialists

**At implementation review** (`implemented` just marked done):
1. Run `git diff main...HEAD --name-only` to get changed file paths
2. Match path patterns from the table above
3. Also re-check task description for any specialist not already detected from files
4. Collect all matched specialists

If no specialists are detected, proceed with the standard chain only (regression → compliance → developer → qa).

---

## Agent auto-chain

After each `done` call, invoke the review agents in order before marking the next step done.
Gather context before invoking — agents need the diff and plan, not just the code.

### Standard chain (always runs)

| Step just marked done | Invoke agent | Context to pass | Approves → auto-mark |
|-----------------------|-------------|-----------------|----------------------|
| `plan_written` | `compliance` + detected specialists | plan file contents | `plan_approved` |
| `implemented` | `regression` | `git diff main...HEAD` + `get_impact_radius` | `regression` |
| `regression` | `compliance` | plan file contents + `git diff main...HEAD` | `compliance` |
| `compliance` | `developer` | `git diff main...HEAD` | `developer` |
| `developer` | `qa` | `git diff main...HEAD` | `qa` |
| `qa` | detected specialists (from implementation signals) | `git diff main...HEAD` | `specialist` |
| `specialist` | — | — | pause for user |
| `user_review` | — | — | `merged` (after squash merge) |

**Plan review order** — after `plan_written`, run in parallel if possible:
1. `compliance` — is the plan achievable? any gaps?
2. Detected specialists — is the design correct for this domain?

All must APPROVE before marking `plan_approved`. If any BLOCK, stop and report.

**Implementation review order** — after `qa`, run detected specialists sequentially:
- `architect` first (if detected) — service boundary and contract correctness
- `ml-developer` (if detected) — inference and embedding patterns
- `a2a-specialist` (if detected) — agent and MCP tool design
- `api-security` (if detected) — auth and credential handling

Each must APPROVE before the next runs. First BLOCK stops the chain.

### Context-gathering commands

Run these before invoking agents — do not pass raw file lists, pass actual content:

```bash
# Full diff from branch start
git diff main...HEAD

# Changed file paths only (for specialist detection)
git diff main...HEAD --name-only

# Plan file — path is in tasks/queue.json current.plan
# Read it with the Read tool

# Impact radius (code-review-graph MCP tool)
# Call get_impact_radius with the list of changed file paths
```

### Chain behavior

- **APPROVED** — mark the step done, continue to next agent automatically
- **BLOCKED** — stop the chain immediately, show all issues to the user, do not mark done
- **User checkpoint** — always stop at `user_review`; show a verdict summary from every agent before asking

### Example: ML task — full chain after `/task done implemented`

```
detect specialists from git diff --name-only:
  training/fine_tune.py, services/matcher/src/embedder.py → ml-developer

1. gather: git diff main...HEAD + get_impact_radius
2. invoke regression → APPROVED → mark regression done
3. gather: plan + git diff
4. invoke compliance → APPROVED → mark compliance done
5. gather: git diff
6. invoke developer → APPROVED → mark developer done
7. gather: git diff
8. invoke qa → APPROVED → mark qa done
9. gather: git diff
10. invoke ml-developer → BLOCKED (batched inference missing, calling model per-item in loop)
11. STOP — report to user
```

### Example: API + A2A task — plan review after `/task done plan_written`

```
detect specialists from task description "add OAuth login via A2A dispatch":
  "OAuth", "auth" → api-security
  "A2A", "dispatch" → a2a-specialist

1. gather: plan file contents
2. invoke compliance → APPROVED
3. invoke api-security → APPROVED
4. invoke a2a-specialist → BLOCKED (AgentCard missing required auth field)
5. STOP — do not mark plan_approved, report to user
```

---

## `/task extract-plan [plan-file]`

Auto-parses the plan file for subtasks and creates dependency-linked queue entries.

Use this after `plan_written` to populate subtasks from your plan.

### Plan format

Write a `### Subtasks` section in your plan:

```markdown
### Subtasks
1. Setup database schema
2. Add repository layer (depends on: Setup database schema)
3. Add service layer (depends on: Add repository layer)
4. Add API endpoints (depends on: Add service layer)
5. Integration tests (depends on: Add service layer)
```

Rules:
- Numbered list under `### Subtasks` heading
- Description must match exactly for dependency resolution
- `(depends on: X, Y, Z)` is optional; omit if no prerequisites
- Order = execution priority among equally-ready tasks

### Behavior

1. Read the plan file (auto-uses `current.plan` if no arg)
2. Parse `### Subtasks` section
3. Resolve dependency names → task ids
4. Create all subtask entries in queue with `status: "ready"` or `"blocked"`
5. `git commit -m "task: extract plan — N subtasks"`
6. Print summary: list all subtasks with their dependency status

## `/task resume`

Auto-pick the next ready task and make it current.

When no task is in progress:
1. Scan queue in order for first task with `status === "ready"` (no unmet deps)
2. Move it from queue → current, commit
3. Show task details: description, branch, plan, next step
4. If all tasks blocked: show what they're waiting on
5. If queue empty: say "Queue is empty"

This lets the user just call `/task resume` without caring about the queue structure.

## `/task merge`

Squash-merge the current branch to main and clean up. Run this after user approves at `user_review`.

```bash
# 1. Capture task description for commit message
TASK_DESC=$(node scripts/task.js current-desc)

# 2. Squash merge to main
git checkout main
git merge --squash <current-branch>
git commit -m "<imperative summary of task>"

# 3. Push and delete branch
git push origin main
git push origin --delete <current-branch>
git branch -d <current-branch>

# 4. Mark merged in queue
node scripts/task.js done merged
```

Rules:
- Always squash merge — one commit per task on main (trunk-based)
- Commit message: imperative verb + what changed (max 72 chars), no "merge:" prefix
- Never push to main without all review agents having APPROVED
- After merge, call `/tasks finish` to unblock dependent tasks

## `/task finish`

Complete the current task and resolve blocked dependencies. Run after `/task merge`.

1. Archive current → `completed[]`
2. Scan queue: any task whose `depends_on` list is now fully satisfied gets `status = "ready"`
3. `git commit -m "task: finish — <desc>"`
4. Print: completed count, newly unblocked tasks, next ready task (if any)

## `/task queue <description>`

Manually add a standalone task to the queue (no subtask extraction).

1. Append to `queue[]` with `status = "ready"` and empty `depends_on`
2. `git commit -m "task: queue — <description>"`
3. Show queue depth

Prefer `extract-plan` for multi-branch work. Use `queue` only for independent tasks.

## `/task next`

Print handoff prompt for local LLM — copy-paste ready.

Shows: task name, branch, plan file, completed steps, next step, instructions.

## `/task list`

Show full queue state: current task, queued tasks (with ready/blocked status), last 5 completed.

Subtasks shown with `↳` prefix. Blocked tasks annotated with their dependencies.

---

## Workflow

### For single-branch tasks

```bash
/tasks start "add login endpoint"
# ... write plan ...
/tasks done plan_written
# ↑ auto-runs: compliance reviews plan → if approved, marks plan_approved
# ... implement (TDD) ...
/tasks done implemented
# ↑ auto-runs: regression → compliance → developer → qa → specialist (if any)
# ... chain stops at user_review for your sign-off ...
/tasks merge        # squash merge to main, delete branch, push
/tasks finish       # archive task, unblock dependents
```

### For multi-branch tasks

```bash
/tasks start "build auth service"
# ... write plan with ### Subtasks section ...
/tasks done plan_written
# ↑ auto-runs: compliance reviews plan → if approved, marks plan_approved
/tasks extract-plan             # auto-parses plan, creates subtasks with deps
/tasks merge                    # squash merge plan + scaffold to main, delete branch
/tasks finish                   # archive plan task, unblock subtasks

# Later, when ready to implement a subtask:
/tasks resume                   # picks first ready subtask, creates branch
# ... implement subtask ...
/tasks done implemented         # auto-runs full review chain
/tasks merge                    # squash merge subtask to main
/tasks finish                   # auto-unblocks dependent subtasks
/tasks resume                   # picks next ready subtask
# ... repeat ...
```

---

## Rules

- Always read the actual file — do not rely on memory of prior queue state
- Commit queue.json after every state change
- Never mark a step done without evidence it was actually completed
- `specialist` step: mark done only if a specialist agent was declared in the task plan and has approved; skip if not applicable
- Write subtasks in the plan file: `### Subtasks` section with optional `(depends on: ...)`
- After `plan_written` step: run `/task extract-plan` to register subtasks from the plan
- When no current task: run `/task resume` to start the next ready task automatically
- Do not call `/task queue` for subtasks — use the plan format instead
- If any agent in the chain is BLOCKED: stop immediately, do not run remaining agents, report all issues together
