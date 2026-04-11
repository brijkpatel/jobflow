#!/usr/bin/env python3
"""
Scan repo to generate contracts/impact-map.json.
Detects: Kafka topic names, MCP tool names, A2A card names, proto imports.
Run after adding new services or contracts.
Usage: python gen-impact-map.py
"""
import ast
import json
import re
import subprocess
from pathlib import Path


def get_repo_root() -> Path:
    return Path(subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], text=True
    ).strip())


def get_services(repo_root: Path) -> list[str]:
    services_dir = repo_root / "services"
    if not services_dir.exists():
        return []
    return [d.name for d in services_dir.iterdir() if d.is_dir()]


def get_contract_artifacts(repo_root: Path) -> list[str]:
    contracts_dir = repo_root / "contracts"
    if not contracts_dir.exists():
        return []
    return [
        str(f.relative_to(repo_root))
        for f in contracts_dir.rglob("*")
        if f.is_file() and not f.name.startswith(".")
    ]


def scan_service_for_artifact(service_path: Path, artifact_name: str) -> bool:
    """Check if a service references an artifact by name (string or import)."""
    artifact_stem = Path(artifact_name).stem  # e.g. "classified-jobs" from path
    pattern = re.compile(re.escape(artifact_stem), re.IGNORECASE)

    for src_file in service_path.rglob("*.py"):
        try:
            if pattern.search(src_file.read_text()):
                return True
        except Exception:
            continue
    return False


def build_impact_map(repo_root: Path) -> dict:
    services = get_services(repo_root)
    artifacts = get_contract_artifacts(repo_root)
    impact_map = {}

    for artifact in artifacts:
        consumers = []
        artifact_stem = Path(artifact).stem
        for svc in services:
            svc_path = repo_root / "services" / svc
            if scan_service_for_artifact(svc_path, artifact_stem):
                consumers.append(svc)
        if consumers:
            impact_map[artifact] = consumers

    return impact_map


def main():
    repo_root = get_repo_root()
    print("Scanning for contract consumers...")
    impact_map = build_impact_map(repo_root)

    out_path = repo_root / "contracts" / "impact-map.json"
    out_path.write_text(json.dumps(impact_map, indent=2))
    print(f"Written to {out_path}")
    print(f"Found {len(impact_map)} contract artifacts with consumers.")


if __name__ == "__main__":
    main()
