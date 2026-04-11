#!/usr/bin/env python3
"""
Query contracts/impact-map.json to find services affected by changed files.
Usage: python impact-analysis.py file1 file2 ...
       python impact-analysis.py --from-git-diff   (reads git diff --name-only)
"""
import json
import subprocess
import sys
from pathlib import Path


def load_map(repo_root: Path) -> dict:
    impact_map_path = repo_root / "contracts" / "impact-map.json"
    if not impact_map_path.exists():
        return {}
    return json.loads(impact_map_path.read_text())


def service_from_path(file_path: str) -> str | None:
    parts = Path(file_path).parts
    if len(parts) >= 2 and parts[0] == "services":
        return parts[1]
    return None


def get_affected(changed_files: list[str], impact_map: dict) -> dict:
    affected_services = set()
    contract_hits = []

    for f in changed_files:
        # Check contract impact map (string-reference deps)
        if f in impact_map:
            consumers = impact_map[f]
            affected_services.update(consumers)
            contract_hits.append({"file": f, "consumers": consumers})

        # Service-local change
        svc = service_from_path(f)
        if svc:
            affected_services.add(svc)

    return {"affected_services": sorted(affected_services), "contract_hits": contract_hits}


def main():
    repo_root = Path(subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], text=True
    ).strip())

    if "--from-git-diff" in sys.argv:
        changed = subprocess.check_output(
            ["git", "diff", "--name-only", "HEAD~1"], text=True
        ).strip().splitlines()
    else:
        changed = [a for a in sys.argv[1:] if not a.startswith("--")]

    if not changed:
        print(json.dumps({"affected_services": [], "contract_hits": []}))
        return

    impact_map = load_map(repo_root)
    result = get_affected(changed, impact_map)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
