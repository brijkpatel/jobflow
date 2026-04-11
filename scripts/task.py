#!/usr/bin/env python3
"""
Task queue manager — persists progress across sessions and LLM handoffs.

Usage:
  task.py status                          show current task and next step
  task.py start <description>            create task from current branch + plan
  task.py done <step>                    mark a step complete and commit state
  task.py finish                         mark task merged, move to completed
  task.py queue <description>            add task to queue (no branch yet)
  task.py next                           print handoff prompt for local LLM
  task.py list                           show full queue

Steps (in order):
  plan_written, plan_approved, implemented,
  regression, compliance, developer, qa, specialist, user_review, merged
"""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

STEPS = [
    "plan_written", "plan_approved", "implemented",
    "regression", "compliance", "developer", "qa",
    "specialist", "user_review", "merged"
]

STEP_DESCRIPTIONS = {
    "plan_written":  "L3 task plan written (writing-plans skill)",
    "plan_approved": "Plan approved by compliance agent",
    "implemented":   "Implementer subagent done (TDD — all tests pass)",
    "regression":    "Regression agent passed (blast radius + affected test suites)",
    "compliance":    "Compliance agent passed (diff matches plan)",
    "developer":     "Developer agent passed (code quality + SOLID)",
    "qa":            "QA agent passed (test coverage + correctness)",
    "specialist":    "Role-specific agent passed (architect/ml/a2a/api-security)",
    "user_review":   "User reviewed and approved",
    "merged":        "Squash merged to main, branch deleted",
}


def repo_root() -> Path:
    r = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
    return Path(r)


def queue_path() -> Path:
    return repo_root() / "tasks" / "queue.json"


def load() -> dict:
    p = queue_path()
    if not p.exists():
        return {"current": None, "queue": [], "completed": []}
    return json.loads(p.read_text())


def save(data: dict):
    p = queue_path()
    p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps(data, indent=2))


def commit(msg: str):
    root = repo_root()
    subprocess.run(["git", "add", str(queue_path())], cwd=root)
    subprocess.run(["git", "commit", "-m", msg], cwd=root)


def current_branch() -> str:
    return subprocess.check_output(["git", "branch", "--show-current"], text=True).strip()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def find_plan(branch: str) -> str:
    """Try to find a plan file for this branch."""
    root = repo_root()
    parts = branch.replace("task/", "").split("/")
    service = parts[0] if parts else ""
    candidates = [
        root / "services" / service / "docs" / "plans",
        root / "docs" / "plans",
    ]
    for d in candidates:
        if d.exists():
            plans = sorted(d.glob("*.md"), reverse=True)
            if plans:
                return str(plans[0].relative_to(root))
    return "docs/plans/<add-plan-path>"


def cmd_start(args: list[str]):
    if not args:
        print("Usage: task.py start <description>")
        sys.exit(1)
    description = " ".join(args)
    data = load()
    if data["current"]:
        print(f"ERROR: task already in progress: {data['current']['description']}")
        print("Run 'task.py finish' to complete it first.")
        sys.exit(1)

    branch = current_branch()
    task_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")

    data["current"] = {
        "id": task_id,
        "description": description,
        "branch": branch,
        "plan": find_plan(branch),
        "steps": {s: False for s in STEPS},
        "last_completed": None,
        "started": now(),
        "updated": now(),
    }
    save(data)
    commit(f"task: start — {description}")
    print(f"Started task [{task_id}]: {description}")
    print(f"Branch: {branch}")
    print(f"Next step: plan_written")


def cmd_done(args: list[str]):
    if not args:
        print("Usage: task.py done <step>")
        print(f"Steps: {', '.join(STEPS)}")
        sys.exit(1)
    step = args[0]
    if step not in STEPS:
        print(f"Unknown step: {step}. Valid: {', '.join(STEPS)}")
        sys.exit(1)

    data = load()
    if not data["current"]:
        print("No task in progress. Run 'task.py start <description>'")
        sys.exit(1)

    task = data["current"]
    task["steps"][step] = True
    task["last_completed"] = step
    task["updated"] = now()
    save(data)
    commit(f"task: step done — {step}")

    # Show next step
    next_step = next((s for s in STEPS if not task["steps"][s]), None)
    if next_step:
        print(f"✓ {step}")
        print(f"→ Next: {next_step} — {STEP_DESCRIPTIONS[next_step]}")
    else:
        print(f"✓ {step}")
        print("All steps complete. Run 'task.py finish' after merging.")


def cmd_finish(args: list[str]):
    data = load()
    if not data["current"]:
        print("No task in progress.")
        sys.exit(1)
    task = data["current"]
    task["steps"]["merged"] = True
    task["last_completed"] = "merged"
    task["updated"] = now()
    data["completed"].append(task)
    data["current"] = None

    # Promote next from queue
    if data["queue"]:
        print(f"Next queued task: {data['queue'][0]['description']}")

    save(data)
    commit(f"task: finish — {task['description']}")
    print(f"✓ Task completed: {task['description']}")
    print(f"  Completed tasks: {len(data['completed'])}")
    print(f"  Queued tasks: {len(data['queue'])}")


def cmd_queue(args: list[str]):
    if not args:
        print("Usage: task.py queue <description>")
        sys.exit(1)
    description = " ".join(args)
    data = load()
    task_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    data["queue"].append({"id": task_id, "description": description, "status": "queued"})
    save(data)
    commit(f"task: queue — {description}")
    print(f"Queued [{task_id}]: {description}")
    print(f"Queue depth: {len(data['queue'])}")


def cmd_status(args: list[str]):
    data = load()
    task = data["current"]
    if not task:
        print("No task in progress.")
        if data["queue"]:
            print(f"\nQueued ({len(data['queue'])}):")
            for t in data["queue"]:
                print(f"  • {t['description']}")
        return

    completed_steps = [s for s in STEPS if task["steps"].get(s)]
    remaining_steps = [s for s in STEPS if not task["steps"].get(s)]
    next_step = remaining_steps[0] if remaining_steps else None

    print(f"Task:    {task['description']}")
    print(f"Branch:  {task['branch']}")
    print(f"Plan:    {task['plan']}")
    print(f"Done:    {', '.join(completed_steps) or 'none'}")
    if next_step:
        print(f"Next:    {next_step} — {STEP_DESCRIPTIONS[next_step]}")
    else:
        print("Next:    merge and run 'task.py finish'")

    if data["queue"]:
        print(f"\nQueued ({len(data['queue'])}):")
        for t in data["queue"]:
            print(f"  • {t['description']}")


def cmd_next(args: list[str]):
    """Print a handoff prompt suitable for a local LLM to continue work."""
    data = load()
    task = data["current"]
    if not task:
        print("No task in progress.")
        sys.exit(1)

    remaining = [s for s in STEPS if not task["steps"].get(s)]
    next_step = remaining[0] if remaining else None

    print("=" * 60)
    print("TASK HANDOFF — resume from here")
    print("=" * 60)
    print(f"Task:          {task['description']}")
    print(f"Branch:        {task['branch']}")
    print(f"Plan:          {task['plan']}")
    print(f"Last done:     {task['last_completed'] or 'nothing yet'}")
    if next_step:
        print(f"Next step:     {next_step}")
        print(f"Description:   {STEP_DESCRIPTIONS[next_step]}")
    print()
    print("Instructions:")
    print(f"  1. git checkout {task['branch']}")
    print(f"  2. Read the plan: {task['plan']}")
    print(f"  3. Complete step: {next_step}")
    print(f"  4. Run: python scripts/task.py done {next_step}")
    print(f"  5. Run: python scripts/task.py next  (for the step after that)")
    print()
    print("Do not redo completed steps:", ", ".join(
        s for s in STEPS if task["steps"].get(s)
    ) or "none")
    print("=" * 60)


def cmd_list(args: list[str]):
    data = load()
    print(f"Current:   {data['current']['description'] if data['current'] else 'none'}")
    print(f"Queued:    {len(data['queue'])}")
    for t in data["queue"]:
        print(f"  • [{t['id']}] {t['description']}")
    print(f"Completed: {len(data['completed'])}")
    for t in data["completed"][-5:]:
        print(f"  ✓ {t['description']}")


COMMANDS = {
    "start": cmd_start,
    "done": cmd_done,
    "finish": cmd_finish,
    "queue": cmd_queue,
    "status": cmd_status,
    "next": cmd_next,
    "list": cmd_list,
}

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    fn = COMMANDS.get(cmd)
    if not fn:
        print(__doc__)
        sys.exit(1)
    fn(sys.argv[2:])
