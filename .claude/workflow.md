# Development Workflow

## The Loop

```
[Feature start]
  brainstorm skill → L2 service design
  architect agent reviews L2

[Per task]
  writing-plans skill → L3 task plan
    └─ declares: files, tests, interfaces, which agents review
  compliance agent → is the plan achievable? any gaps?

  git checkout -b task/<service>/<description> main

  implementer subagent (TDD)
    1. write failing test
    2. confirm it fails
    3. write minimal code to pass
    4. all tests pass
    5. commit all changed files

  regression agent   → blast radius + affected service test suites
  compliance agent   → does diff match the plan exactly?
  developer agent    → code quality, SOLID, layer rules
  qa agent           → test coverage, edge cases, test correctness
  [role agent]       → architect / ml-developer / a2a-specialist / api-security
                        (declared in task plan, only if applicable)

  → show user: task name + 2-line summary
  user approves → squash merge to main → delete branch → next task
```

## Rules

- **No output during implementation.** Implementer subagent just implements.
- **Baseline green before starting.** Run full test suite before branching. If it's red, fix first.
- **Sequential tasks only.** One implementer subagent at a time. No parallel implementation.
- **All files in one commit per task.** No partial commits.
- **Never commit to main directly.**
- **Regression runs first.** If tests break, no point running other reviews.
- **Contract changes trigger architect review** regardless of what else changed.

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
