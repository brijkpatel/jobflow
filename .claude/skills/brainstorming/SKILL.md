---
name: brainstorming
description: Socratic design exploration → concrete spec → handoff to writing-plans. Hard gate: no code before a spec exists. Use when requirements are ambiguous, design alternatives exist, or the task crosses service boundaries.
---

# Brainstorming — Design Exploration

This skill produces a **spec doc** that becomes the input to `/forge plan`.  
**No code is written during brainstorming.** The output is always a document.

---

## When to invoke

Invoke before `/forge plan` when:
- The task description is ambiguous or high-level ("build X", "add Y feature")
- Multiple valid design approaches exist and you need to pick one
- The task crosses service boundaries or introduces new contracts
- L2 complexity score ≥ 2 but the design space is still open

Skip brainstorming and go straight to `/forge plan` when:
- The approach is already clear and agreed upon
- The task is a well-scoped L3 bug fix or refactor

---

## Step 1 — Socratic exploration

Ask (and answer) these questions before proposing anything:

**Problem framing**
1. What user/system need does this solve? What's the outcome if we don't build it?
2. What are the constraints? (performance, latency, consistency, cost, team skill)
3. What already exists that we can leverage?

**Design alternatives**
4. What are 2–3 distinct approaches? (at minimum: the obvious one + one alternative)
5. What are the trade-offs for each? (correctness, complexity, testability, operability)
6. Which approach best fits the constraints and codebase conventions? Why?

**Integration and contracts**
7. What service boundaries does this touch?
8. What contracts (proto, Kafka, REST, MCP, A2A) need to be created or changed?
9. What data flows in and out? Where does it come from, where does it go?

**Risks and unknowns**
10. What's the riskiest assumption in the chosen approach?
11. What could go wrong in production? What's the mitigation?
12. Are there any unknowns that must be resolved before implementation?

---

## Step 2 — Write the spec doc

### File location

```
docs/specs/<YYYY-MM-DD>-<slug>-spec.md
```

### Required sections

```markdown
---
type: spec
status: draft
---

## Problem statement

One paragraph: what is this solving, for whom, and why now?

## Chosen approach

State the design decision clearly. This is the answer to "how will we build this?"

## Alternatives considered

| Approach | Trade-offs | Rejected because |
|---|---|---|
| Approach A | ... | ... |
| Approach B | ... | ... |

## Architecture sketch

High-level component diagram (Mermaid or ASCII) showing data flows and service interactions.

## Contracts required

| Artifact | Type | Action |
|---|---|---|
| `foo.proto` | gRPC | new |
| `bar-topic` | Kafka | new |

## Open questions

List anything unresolved. Each must be resolved before `/forge plan` begins.

1. [ ] Should X be sync or async?
2. [ ] Which storage backend — Qdrant or PGVector?
```

---

## Step 3 — Resolve open questions

Do not hand off to planning while any open questions remain.

For each open question:
- Search the codebase for existing patterns
- Check `docs/plans/` for prior decisions
- Consult architecture docs (`docs/plans/system-architecture.md`, `contracts/`)
- If still unresolved, ask the user directly (one question at a time)

Update the spec doc: mark `[x]` when resolved, add the decision inline.

---

## Step 4 — Handoff to planning

Once all open questions are resolved and the spec is approved:

```
Spec saved at: docs/specs/<date>-<slug>-spec.md

Next: run /forge plan — the writing-plans skill will use this spec as input.
Reference the spec in the plan's "Solution approach" section.
```

The brainstorming skill does **not** invoke `/forge plan` automatically — it produces a spec that you then feed into the planning phase.

---

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| Jumping to code without a spec | Stop — write the spec first |
| Listing 5+ alternatives without picking one | Pick one, explain why, discard the rest |
| Vague "we'll figure it out later" open questions | Name the decision, research it, answer it now |
| Over-engineering the spec (10-page design doc for a 2-hour task) | If it fits in 1 page, write 1 page |
| Spec that restates the task description without adding clarity | Every section must add information beyond the task description |
