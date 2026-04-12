---
name: writing-plans
description: Write an L3 task plan — the source of truth for an implementation task. Invoked by /forge plan before any code is written.
---

# Writing L3 Task Plans

An L3 plan is the **contract between planning and implementation**. Every reviewer agent (compliance, developer, qa, specialists) checks the diff against this plan. Write it once, precisely, before touching any code.

---

## When to invoke this skill

After `/forge start <description>` and before writing any code. The forge cycle calls this skill as part of `/forge plan`.

---

## Step 1 — Gather context (do all of these before writing anything)

```bash
# 1. Task description and branch
node scripts/task.js status

# 2. Git diff from main (should be empty at planning time — verify)
git diff main...HEAD --name-only

# 3. Service being modified (infer from branch name: task/<service>/...)
# Read the service entry point and existing structure

# 4. Relevant contracts (always check these)
ls contracts/proto/
ls contracts/kafka/schemas/
ls contracts/mcp/tools/
ls contracts/a2a/cards/
ls contracts/migrations/

# 5. Existing plans for this service
ls services/<service>/docs/plans/ 2>/dev/null || ls docs/plans/

# 6. Related L2 design doc (if it exists)
ls docs/plans/system-architecture.md
ls services/<service>/docs/ 2>/dev/null

# 7. Impact radius — what depends on the service being changed
# Use code-review-graph: get_impact_radius on the service directory
```

Read all relevant files before forming the solution approach. Do not guess at interfaces — look them up.

---

## Step 2 — Specialist pre-detection

Before writing the plan, detect which specialists will need to review it. This shapes the solution approach.

| If the task involves... | Specialist needed |
|---|---|
| New service, Kafka schema/topic, proto change, migration, cross-service contract, A2A card | `architect` |
| LLM inference, embeddings, RAG, vector search, fine-tuning, Gemma, classifier | `ml-developer` |
| A2A protocol, ADK agents, MCP tool definitions, AgentCard, orchestration | `a2a-specialist` |
| Auth, JWT, OAuth, tokens, secrets, credential handling, public endpoints | `api-security` |

Write detected specialists into the `reviewers:` frontmatter.

---

## Step 3 — Write the plan

### File location

```
services/<service>/docs/plans/<YYYY-MM-DD>-<slug>.md   # for service-scoped tasks
docs/plans/<YYYY-MM-DD>-<slug>.md                       # for cross-cutting tasks
```

Create the directory if it doesn't exist.

### Required sections (do not omit any)

```markdown
---
task: <short imperative name — matches branch suffix>
reviewers: developer, qa, compliance, regression[, architect][, ml-developer][, a2a-specialist][, api-security]
branch: task/<service>/<description>
---

## Problem

What is broken, missing, or needs to change? One paragraph, specific. Link to issue if applicable.
Do NOT describe the solution here — only the problem.

## Solution approach

How will you solve it? State the chosen approach and why.
If you considered alternatives, name them and explain why you rejected them (one line each).
Call out any non-obvious design decisions.

## Interfaces & contracts

List every interface, proto, Kafka schema, MCP tool, A2A card, SQL migration, or public API that
will be **created or modified**. Be exact — the architect agent checks this section.

| Artifact | Change | File |
|---|---|---|
| `ResumeService.ParseResume` (gRPC) | add `language` field to request | `contracts/proto/resume.proto` |
| `raw-jobs` Kafka topic | no change | — |
| (add rows for every contract change, or write "No contract changes") |

If there are no contract changes, write: **No contract changes.**

## Files to change

List every file that will be created, modified, or deleted. Be complete — compliance agent diffs
this list against the actual PR.

| File | Action | What changes |
|---|---|---|
| `services/foo/src/bar.py` | modify | add `parse_language()` method |
| `services/foo/tests/test_bar.py` | create | unit tests for `parse_language()` |
| `services/foo/docs/plans/2026-04-12-foo.md` | create | this plan |

Do not list `tasks/queue.json` — it is always implicitly changed.

## Test strategy

For each new/modified behaviour, specify:
- **What** is being tested (the behaviour, not the implementation)
- **Type** (unit / integration / e2e)
- **Where** (file path)
- **Happy path + at least one failure/edge case per behaviour**

Example:
- Unit — `test_parse_language_detects_english()` in `tests/test_bar.py` — happy path
- Unit — `test_parse_language_returns_unknown_on_empty_input()` — edge case
- Integration — `test_resume_pipeline_with_language_field()` in `tests/integration/` — full flow

Do not write "tests will be written" — write the actual test names.

## Acceptance criteria

Concrete, observable conditions that define "done". Each item must be independently verifiable.

- [ ] `ParseResume` returns `language` field populated for English and Spanish resumes
- [ ] All new unit tests pass (`uv run pytest services/foo/`)
- [ ] No regression in existing tests
- [ ] gRPC contract version bumped if breaking change

## Out of scope

Explicitly state what this task will NOT do. Prevents scope creep and reviewer confusion.

- Language detection for non-Latin scripts (follow-up task)
- UI changes — API only
- Updating existing stored resumes with language field

### Subtasks

(Only add this section if the task decomposes into sequential implementation units.
Leave it out for single-unit tasks.)

1. First subtask — description
2. Second subtask — description (depends on: First subtask)
3. Third subtask — description (depends on: Second subtask)

Rules for subtasks:
- Each subtask must be independently testable and committable
- Dependency names must match exactly (used by `/forge extract-plan`)
- Order them by natural implementation sequence
- Aim for subtasks of roughly equal size
- Never create a subtask just for "tests" — tests live inside the subtask they cover
```

---

## Step 4 — Validate the plan before saving

Run this mental checklist before writing the file:

**Completeness**
- [ ] Every behaviour in the solution approach maps to at least one file in "Files to change"
- [ ] Every file in "Files to change" maps to at least one test in "Test strategy"
- [ ] Every contract change is in "Interfaces & contracts"
- [ ] Acceptance criteria are observable (not "works correctly")

**Scope discipline**
- [ ] No files listed that aren't part of this task's change
- [ ] "Out of scope" mentions anything adjacent that might be confused as in-scope
- [ ] Subtasks cover the full solution — nothing falls through the cracks

**Reviewer alignment**
- [ ] `reviewers:` frontmatter includes all detected specialists
- [ ] If contract changes exist, `architect` is in reviewers

**Forge compatibility**
- [ ] `### Subtasks` section uses numbered list format (for `/forge extract-plan`)
- [ ] Dependency names match subtask descriptions exactly

---

## Step 5 — After writing the plan

```bash
# Update the plan path in queue.json if it was a placeholder
# (forge does this automatically if you used /forge plan)

# Then invoke forge to complete the step
# Do NOT run this yet — wait for user to verify the plan
echo "Plan written. Review it at <path>, then run: /forge done plan_written"
```

The plan is reviewed by `compliance` + detected specialists as part of `/forge done plan_written`.
Do not mark `plan_written` done until the file is saved and the user has had a chance to review it.

---

## Common mistakes

| Mistake | Fix |
|---|---|
| Writing "add tests" without specifying test names | Name each test function explicitly |
| Listing files you might touch "just in case" | Only list files you will definitely change |
| Vague acceptance criteria ("it works") | Make each criterion independently verifiable |
| Missing a contract change in "Interfaces & contracts" | Architect catches this — better to catch it in planning |
| Forgetting `(depends on: ...)` in subtasks | `/forge extract-plan` will create independent tasks when deps exist |
| Over-scoping ("while we're here, let's also...") | Put it in "Out of scope", queue a follow-up task |
| Writing the solution in "Problem" | Problem = what's wrong; Solution = how to fix it |
