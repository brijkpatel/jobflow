---
name: task
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
- `user_review`   — User reviewed and approved
- `merged`        — Squash merged to main, branch deleted

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

Mark a step complete and show the next one.

1. Set `steps.<step> = true` and `last_completed = <step>`
2. `git commit -m "task: step done — <step>"`
3. Show next incomplete step

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

## `/task finish`

Complete the current task and resolve blocked dependencies.

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
/task start "add login endpoint"
# ... do plan_written step ...
/task done plan_written
# ... continue through steps ...
/task finish
```

### For multi-branch tasks

```bash
/task start "build auth service"
# ... write plan with ### Subtasks section ...
/task done plan_written
/task extract-plan              # auto-parses plan, creates subtasks with deps
/task finish                    # mark plan-writing complete, move to next step

# Later, when ready to implement:
/task resume                    # picks first ready subtask
# ... implement subtask 1 ...
/task finish                    # auto-unblocks dependent subtasks
/task resume                    # picks next ready subtask
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
