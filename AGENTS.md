# Agent Instructions

Run `./init.sh` before any development. The script prints every Markdown file so you ingest the project context, installs Python requirements, and sets up pre-commit hooks. Keep all documentation synchronized with code so future agents stay aware of the project state. When introducing new features or refactoring—even without explicit user prompts—add tests, bump the version, and document the behavior.

`init.sh` also generates `context_snapshot.md`, `context_snapshot.json`, `code_snapshot.md`, and `code_snapshot.json`. Ensure these files are regenerated and committed whenever documentation or source code changes.

From the repository root execute:

1. `./init.sh`
2. `pre-commit run --all-files`
3. `ruff check ZDownloadManager`
4. `python -m py_compile $(find ZDownloadManager -name '*.py')`
5. `(cd ZDownloadManager && python -m zdownloadmanager.cli --help)`
6. `(cd ZDownloadManager && python -m unittest discover tests -v)`

All changes must update relevant documentation and maintain version numbers.

Set `GITHUB_TOKEN` when using the GitHub automation scripts or tests that
interact with the GitHub API.
