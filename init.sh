#!/bin/sh
set -e
find . -name '*.md' -print | while read -r file; do
  printf '\n===== %s =====\n' "$file"
  cat "$file"
done
pip install -r requirements.txt
pre-commit install >/dev/null 2>&1 || true
python scripts/context_snapshot.py >/dev/null 2>&1 || true
python scripts/code_scan.py >/dev/null 2>&1 || true
