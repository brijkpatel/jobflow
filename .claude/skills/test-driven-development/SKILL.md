---
name: test-driven-development
description: RED-GREEN-REFACTOR implementation discipline. Iron law — never write implementation code before a failing test. Invoked by the implementer subagent during the `implemented` step.
---

# Test-Driven Development

**Iron law: no implementation code exists before a failing test proves it is needed.**

If you find yourself writing implementation code without a red test, stop. Delete the implementation. Write the test first.

---

## The TDD cycle

```
RED   → write a failing test that describes the desired behaviour
GREEN → write the minimum code to make it pass (no more)
REFACTOR → clean up without changing behaviour (tests stay green)
```

Repeat for every behaviour. One cycle = one commit.

---

## Step 1 — Read the plan

Before writing anything:

```bash
node scripts/task.js status   # get plan file path
cat <plan-file>               # read: test strategy, files to change, acceptance criteria
```

Extract the test list from `## Test strategy`. These are your RED tests, in order.

---

## Step 2 — RED (write failing test first)

Pick the first test from the plan's `## Test strategy`. Write **only** the test — no implementation yet.

```bash
uv run pytest <test-file>::<test-name> -v   # must FAIL here
```

If the test passes without implementation code: the test is wrong. Fix it.

Rules:
- Test one behaviour at a time
- Tests must be deterministic (no sleep, no random, no network in unit tests)
- Use fixtures, not global state
- Test the **behaviour** (inputs → outputs), not the implementation
- Name tests: `test_<what>_<when>_<expected_outcome>()`

---

## Step 3 — GREEN (minimum implementation)

Write the minimum code that makes the failing test pass.

```bash
uv run pytest <test-file>::<test-name> -v   # must PASS here
```

"Minimum" means:
- Do not add functionality not tested yet
- Do not optimise yet
- Hard-coded values are fine at this stage (you'll generalize in REFACTOR or next RED)
- If you write more code than the test requires, delete the excess

---

## Step 4 — REFACTOR (clean without breaking)

Clean up the implementation. Tests must stay green throughout.

```bash
uv run pytest <test-file> -v   # all tests must stay green after every refactor step
```

Refactor checklist:
- [ ] Remove duplication
- [ ] Rename for clarity
- [ ] Extract helpers or classes if the function exceeds ~30 lines
- [ ] Apply domain conventions (see `.claude/coding-standards.md`)
- [ ] No framework imports in domain layer

---

## Step 5 — Repeat for next test

Pick the next test from the plan. Go back to RED.

When all tests from the plan are green:

```bash
uv run pytest services/<service>/   # full suite — must be green
```

---

## Commit discipline

Commit after each GREEN-REFACTOR cycle:

```bash
git add <files>
git commit -m "feat: <behaviour> — tests pass"
```

Do not batch multiple behaviours into one commit.

---

## Finishing the implemented step

When all acceptance criteria from the plan are met and all tests pass:

```bash
uv run pytest services/<service>/ -v --tb=short   # must show all green

# then:
/forge done implemented
```

---

## Anti-patterns

| Anti-pattern | Fix |
|---|---|
| Writing implementation before any test | Delete implementation. Write test first. |
| Tests that always pass (no assertion, wrong mock) | Run without implementation — if it passes, it's wrong |
| Testing implementation details (mocking internals) | Test public interface behaviour |
| One giant test that tests everything | One test per behaviour |
| Skipping REFACTOR to ship faster | Tech debt compounds — always refactor before moving on |
| `# TODO: add tests later` | No. Tests come first. Always. |
