---
name: subagent-driven-development
description: Fresh subagent per task — no context bleed between tasks. Two-stage review: spec compliance then code quality. Use for the `implemented` step when a task has subtasks queued.
---

# Subagent-Driven Development

Each implementation task gets a **fresh subagent** with the full context it needs.  
Subagents do not share state. When a subagent finishes, its output is reviewed before the next task begins.

---

## When to use this skill

Use this skill during the `implemented` step when:
- The current task has subtasks in the queue (`task.subtask_ids.length > 0`)
- You are starting a task that was extracted from an L2 or L3 plan
- The implementation is large enough that context bleed between phases would be risky

For small single-unit tasks, implement directly without this skill.

---

## Subagent spawn protocol

### Before spawning

```bash
node scripts/task.js status    # confirm current task + plan path
node scripts/task.js next      # prints the handoff block for the subagent
```

The `task next` output contains everything the subagent needs:
- Task description
- Plan file path and contents
- Branch name
- Next step
- Acceptance criteria

### What to give the subagent

Pass the full handoff block plus:
1. **Plan file contents** — copy the full markdown
2. **Relevant source files** — list file paths from `## Files to change` in the plan
3. **Test strategy** — the full `## Test strategy` section
4. **Acceptance criteria** — the full `## Acceptance criteria` section
5. **Coding standards** — reference `.claude/coding-standards.md`
6. **TDD instruction** — the subagent must follow the `test-driven-development` skill

Do NOT pass:
- Files not mentioned in the plan
- Previous task context or conversation history
- Your own implementation notes

---

## Subagent instructions template

```
You are implementing: <task description>

Branch: <branch>
Plan: <plan-file-path>

## Your task
<paste ## Problem section from plan>

## Solution approach
<paste ## Solution approach section from plan>

## Files to change
<paste ## Files to change table from plan>

## Test strategy
<paste ## Test strategy section from plan>

## Acceptance criteria
<paste ## Acceptance criteria section from plan>

## Rules
- Follow test-driven-development skill: RED-GREEN-REFACTOR, no code before failing test
- Follow coding-standards.md: domain layer zero framework imports, Protocol over class
- Commit after each GREEN cycle: `git commit -m "feat: <behaviour> — tests pass"`
- When done: run full test suite (`uv run pytest services/<service>/`)
- Report: which acceptance criteria are met, which tests pass, any blockers
```

---

## Two-stage review

After the subagent finishes, run **two separate reviews** before marking `implemented` done:

### Stage 1 — Spec compliance (did the subagent do what the plan said?)

Invoke the `compliance` agent with:
- Plan file contents
- `git diff main...HEAD`

The compliance agent checks:
- Every file in `## Files to change` was actually changed
- Every contract in `## Interfaces & contracts` was implemented correctly
- No files were changed that aren't in the plan
- Acceptance criteria are demonstrably met

**If compliance BLOCKS**: fix the gap before Stage 2.

### Stage 2 — Code quality (is the code well-written?)

Invoke the `developer` agent with:
- `git diff main...HEAD`

The developer agent checks:
- SOLID principles, clean architecture
- No framework imports in domain layer
- Naming conventions
- No dead code, no TODOs, no commented-out code
- Error handling is explicit

**If developer BLOCKS**: fix the issues before proceeding.

---

## After both stages pass

```bash
/forge done implemented
# → triggers regression → compliance → developer → qa → specialist → user_review
```

---

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| Carrying context from one subtask to the next subagent | Fresh subagent each time — pass plan, not memory |
| Skipping Stage 1 to save time | Spec drift compounds — always check compliance first |
| Spawning the subagent without the full plan | Subagent will make assumptions — pass everything |
| Letting the subagent deviate from the plan "because it's better" | Plan deviations require a plan update, not silent changes |
| Not running the full test suite before review | Subagent must prove all tests pass before handoff |
