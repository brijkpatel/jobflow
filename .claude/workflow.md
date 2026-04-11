# Development Workflow

## Session start (always do this first)

```bash
python scripts/task.py status   # check if a task is in progress
```

If a task is in progress: resume from `last_completed` — **do not redo completed steps**.
If nothing is in progress: pick the next item from the queue or start a new task.

## The Loop

```
[Feature start]
  brainstorm skill → L2 service design
  architect agent reviews L2

[Per task]
  writing-plans skill → L3 task plan
    └─ declares: files, tests, interfaces, which agents review
  python scripts/task.py done plan_written

  compliance agent → is the plan achievable? any gaps?
  python scripts/task.py done plan_approved

  git checkout -b task/<service>/<description> main
  python scripts/task.py start "<description>"

  implementer subagent (TDD)
    1. write failing test
    2. confirm it fails
    3. write minimal code to pass
    4. all tests pass
    5. commit all changed files
  python scripts/task.py done implemented

  regression agent   → blast radius + affected service test suites
  python scripts/task.py done regression

  compliance agent   → does diff match the plan exactly?
  python scripts/task.py done compliance

  developer agent    → code quality, SOLID, layer rules
  python scripts/task.py done developer

  qa agent           → test coverage, edge cases, test correctness
  python scripts/task.py done qa

  [role agent if declared] → architect / ml-developer / a2a-specialist / api-security
  python scripts/task.py done specialist

  → show user: task name + 2-line summary
  python scripts/task.py done user_review

  user approves → squash merge to main → delete branch
  python scripts/task.py finish   ← removes from queue, promotes next task
```

## Handing off to local LLM mid-task

If you run out of tokens or want to hand off remaining steps:

```bash
python scripts/task.py next   # prints full handoff prompt — paste into local LLM
```

The prompt tells the LLM: branch, plan file, last completed step, next step, what not to redo.

## Rules

- **Session start: always check task status first.**
- **No output during implementation.** Implementer subagent just implements.
- **Baseline green before starting.** Run full test suite before branching. If it's red, fix first.
- **Sequential tasks only.** One implementer subagent at a time. No parallel implementation.
- **All files + queue.json in one commit per step.**
- **Never commit to main directly.**
- **Regression runs first.** If tests break, no point running other reviews.
- **Contract changes trigger architect review** regardless of what else changed.
- **task.py finish after merge** — keeps queue accurate, promotes next task.

## Agent invocation

Task plan header declares reviewers:

```markdown
## Task: implement Kafka consumer in jobflow-matcher
reviewers: developer, qa, compliance, regression
```

```markdown
## Task: add A2A dispatch to ApplicationAgent
reviewers: developer, qa, compliance, regression, a2a-specialist
```

## Superpowers skills used

| Step | Skill |
|---|---|
| Feature ideation | `superpowers:brainstorming` |
| Write L3 task plan | `superpowers:writing-plans` |
| Execute plan | `superpowers:subagent-driven-development` |
| TDD in implementer | `superpowers:test-driven-development` |
| Code review | `superpowers:requesting-code-review` |
| Branch completion | `superpowers:finishing-a-development-branch` |
| Claim done | `superpowers:verification-before-completion` |
| Debug failing tests | `superpowers:systematic-debugging` |
| Multiple independent failures | `superpowers:dispatching-parallel-agents` |
