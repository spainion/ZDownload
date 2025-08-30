#!/usr/bin/env python3
"""Summarize Python source files for context-aware agents.

This script scans a repository for Python files and collects top-level
classes and functions along with their arguments. The result is written
as both JSON and Markdown to aid quick navigation of the codebase.
"""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Dict, List


def format_args(args: ast.arguments) -> str:
    parts: List[str] = [a.arg for a in args.args]
    if args.vararg:
        parts.append("*" + args.vararg.arg)
    parts.extend(a.arg for a in args.kwonlyargs)
    if args.kwarg:
        parts.append("**" + args.kwarg.arg)
    return ", ".join(parts)


def scan_file(path: Path) -> Dict[str, object]:
    tree = ast.parse(path.read_text())
    functions: List[str] = []
    classes: Dict[str, List[str]] = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            functions.append(f"{node.name}({format_args(node.args)})")
        elif isinstance(node, ast.ClassDef):
            methods: List[str] = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    methods.append(f"{item.name}({format_args(item.args)})")
            classes[node.name] = methods
    return {"functions": functions, "classes": classes}


def generate_summary(root: Path) -> Dict[str, Dict[str, object]]:
    summary: Dict[str, Dict[str, object]] = {}
    for file in sorted(root.rglob("*.py")):
        if ".venv" in file.parts:
            continue
        summary[str(file.relative_to(root))] = scan_file(file)
    return summary


def build_markdown(summary: Dict[str, Dict[str, object]]) -> str:
    lines: List[str] = ["# Code Snapshot", ""]
    for file, info in summary.items():
        lines.append(f"## {file}")
        for func in info["functions"]:
            lines.append(f"- {func}")
        for cls, methods in info["classes"].items():
            lines.append(f"- class {cls}")
            for method in methods:
                lines.append(f"  - {method}")
        lines.append("")
    if lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1], help="Repository root")
    parser.add_argument("--json", type=Path, default=Path("code_snapshot.json"), help="Path to JSON output")
    parser.add_argument("--markdown", type=Path, default=Path("code_snapshot.md"), help="Path to Markdown output")
    parser.add_argument("--check", action="store_true", help="Verify snapshot is up to date")
    args = parser.parse_args()

    summary = generate_summary(args.root)
    json_output = json.dumps(summary, indent=2) + "\n"
    md_output = build_markdown(summary)

    if args.check:
        if not args.json.exists() or not args.markdown.exists():
            raise SystemExit("code snapshot missing; run scripts/code_scan.py")
        if args.json.read_text() != json_output or args.markdown.read_text() != md_output:
            raise SystemExit("code snapshot out of date; run scripts/code_scan.py")
        return

    if args.json.read_text() if args.json.exists() else "" != json_output:
        args.json.write_text(json_output)
    if args.markdown.read_text() if args.markdown.exists() else "" != md_output:
        args.markdown.write_text(md_output)


if __name__ == "__main__":
    main()
