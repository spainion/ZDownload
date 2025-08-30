#!/usr/bin/env python
"""Generate a consolidated context snapshot of documentation and commits."""
from __future__ import annotations

import argparse
import ast
import json
import subprocess
from pathlib import Path

from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]


def build_dependency_map() -> Dict[str, List[str]]:
    """Return a mapping of Python files to in-repo imports."""
    py_files = [p for p in ROOT.rglob("*.py")]
    module_map: Dict[str, Path] = {}
    for path in py_files:
        rel = path.relative_to(ROOT)
        module_map[".".join(rel.with_suffix("").parts)] = rel
    dep_map: Dict[str, List[str]] = {}
    for path in py_files:
        rel = path.relative_to(ROOT)
        module_name = ".".join(rel.with_suffix("").parts)
        deps = set()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except Exception:
            dep_map[str(rel)] = []
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod = alias.name
                    while mod:
                        target = module_map.get(mod)
                        if target:
                            deps.add(str(target))
                            break
                        mod = ".".join(mod.split(".")[:-1])
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ""
                if node.level:
                    parts = module_name.split(".")
                    base = ".".join(parts[:-node.level] + ([node.module] if node.module else []))
                mod = base
                while mod:
                    target = module_map.get(mod)
                    if target:
                        deps.add(str(target))
                        break
                    mod = ".".join(mod.split(".")[:-1])
        dep_map[str(rel)] = sorted(deps)
    return dep_map


def generate_snapshot() -> tuple[str, dict]:
    files = sorted(p for p in ROOT.rglob("*.md") if p.name != "context_snapshot.md")
    sections = []
    file_map = {}
    for path in files:
        rel = path.relative_to(ROOT)
        raw = path.read_text(encoding="utf-8")
        text = "\n".join(line.rstrip() for line in raw.splitlines())
        sections.append(f"# File: {rel}\n\n{text}\n")
        file_map[str(rel)] = text
    deps = build_dependency_map()
    dep_lines = [f"- {f}: {', '.join(d) if d else '[]'}" for f, d in sorted(deps.items())]
    log = subprocess.check_output(["git", "log", "-n", "20", "--skip", "1", "--oneline"], cwd=ROOT, text=True)
    status = subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True)
    combined = (
        "\n".join(sections)
        + "\n## Dependency graph\n\n"
        + "\n".join(dep_lines)
        + "\n\n## Recent commits\n\n"
        + log
        + "\n## Repository status\n\n"
        + (status or "clean\n")
    )
    return combined, {"files": file_map, "dependencies": deps, "log": log, "status": status}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Verify snapshot is up to date")
    args = parser.parse_args()
    md_text, json_data = generate_snapshot()
    md_path = ROOT / "context_snapshot.md"
    json_path = ROOT / "context_snapshot.json"
    md_output = md_text + "\n"
    json_output = json.dumps(json_data, indent=2) + "\n"
    if args.check:
        if not md_path.exists() or not json_path.exists():
            raise SystemExit("context snapshot missing; run scripts/context_snapshot.py")
        if md_path.read_text(encoding="utf-8") != md_output or json_path.read_text(encoding="utf-8") != json_output:
            raise SystemExit("context snapshot out of date; run scripts/context_snapshot.py")
        return
    if md_path.read_text(encoding="utf-8") if md_path.exists() else "" != md_output:
        md_path.write_text(md_output, encoding="utf-8")
    if json_path.read_text(encoding="utf-8") if json_path.exists() else "" != json_output:
        json_path.write_text(json_output, encoding="utf-8")


if __name__ == "__main__":
    main()
