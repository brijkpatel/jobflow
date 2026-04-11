---
name: task
description: Manage the task queue in tasks/queue.json. Check status, start tasks, mark steps done, finish tasks, hand off to local LLM. Invoke at session start and after each workflow step.
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
- Current task: description, branch, plan file
- Completed steps (✓) and remaining steps
- Next step with its description
- Queue depth

If no current task, show queue items.

## `/task start <description>`

1. Read current git branch: `git branch --show-current`
2. Generate id: current datetime YYYYMMDD-HHMM
3. Add to `current` in queue.json with all steps = false
4. Try to find plan file under `services/<service>/docs/plans/` or `docs/plans/`
5. `git add tasks/queue.json && git commit -m "task: start — <description>"`
6. Show next step: `plan_written`

## `/task done <step>`

1. Set `steps.<step> = true` and `last_completed = <step>` in queue.json
2. Update `updated` timestamp
3. `git add tasks/queue.json && git commit -m "task: step done — <step>"`
4. Show next incomplete step with its description

## `/task finish`

1. Move `current` into `completed[]` array in queue.json
2. Set `current = null`
3. `git add tasks/queue.json && git commit -m "task: finish — <description>"`
4. Show next queued task if any

## `/task queue <description>`

1. Append to `queue[]` array in queue.json
2. `git add tasks/queue.json && git commit -m "task: queue — <description>"`
3. Show updated queue depth

## `/task next`

Print a handoff prompt for local LLM — copy-paste ready:

```
TASK HANDOFF
Task:        <description>
Branch:      <branch>
Plan:        <plan file path>
Last done:   <last_completed>
Next step:   <next incomplete step>
What to do:  <step description>

Instructions:
1. git checkout <branch>
2. Read the plan: <plan file>
3. Complete step: <next step>
4. Invoke: /task done <next step>
5. Invoke: /task next

Do NOT redo: <list of completed steps>
```

## `/task list`

Show all sections: current task (with step progress), queued tasks, last 5 completed.

---

## Rules

- Always read the actual file — do not rely on memory of prior queue state
- Commit queue.json after every state change
- Never mark a step done without evidence it was actually completed
- `specialist` step: mark done only if a specialist agent was declared in the task plan and has approved; skip (mark true with note "N/A") if not applicable
