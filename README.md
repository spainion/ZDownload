# ZDownload

ZDownloadManager is a cross-platform download manager and smart file organiser with resume support, mirror fallback and Chrome integration. The application source lives in the `ZDownloadManager/` directory.

## Features
- Resumable downloads with SHA-256 piece verification
- Multi-source downloading with automatic mirror fallback
- Library manager that categorises completed downloads
- Smart filename normalisation and configurable actions
- Optional Chrome extension for browser integration
- OS integration scripts under `ZDownloadManager/install` for Chrome native messaging
  and system context menus on Windows and macOS
- In-app configuration menu to adjust piece size, concurrency, suggestions and
  the OpenRouter API key
- LLM-backed suggestion system with on-disk caching
- Customisable OpenRouter model via `--suggest-model` or config
- Configurable suggestion parameters via `--suggest-temperature`, `--suggest-max-tokens` and `--suggest-top-p`
- `--version` and `--show-config` CLI options for introspection
- `--list-models` flag or `scripts/openrouter_models.py` to list OpenRouter models
- Web scraping helper via `--scrape` to list page links
- GitHub automation helper via `scripts/github_tools.py` to commit files, open pull requests, list issues, list pull requests, and show repository languages
- `--clear-suggestions-cache` flag to purge cached AI responses
- `--suggest-stream` to stream AI answers for a question
- `--show-suggestions-cache` flag to inspect cached AI responses
- Code scanning script `scripts/code_scan.py` and `--context` Makefile target to summarise classes and functions for agents
- Snapshot helpers `--show-context-snapshot`, `--show-code-snapshot` and `--verify-snapshots` for context awareness
- Dependency-aware context snapshot that maps Python imports to highlight affected files
- `--show-dependencies` and `--show-dependents` flags to query module relationships from the context snapshot

## Initialization
```bash
./init.sh
```
The script displays every Markdown file so contributors ingest the current context, installs all Python requirements and sets up pre-commit hooks. It also generates a `context_snapshot` capturing documentation, a Python dependency graph and recent commit history. Update the documentation whenever behaviour changes so subsequent agents remain informed.
It also writes `code_snapshot` files that summarise classes and functions across the repository for quick reference.

## Usage
```bash
# Start the graphical interface
python -m zdownloadmanager.ui.main_window

# Or use the CLI
python -m zdownloadmanager.cli --help

# Ask the AI a question
python -m zdownloadmanager.cli --suggest "What is this project?"
# Ask using a specific model
python -m zdownloadmanager.cli --suggest "What is this project?" --suggest-model openai/gpt-4o-mini
# Stream an answer
python -m zdownloadmanager.cli --suggest-stream "What is this project?"
# Tune suggestion parameters
python -m zdownloadmanager.cli --suggest "What is this project?" --suggest-temperature 0.5 --suggest-max-tokens 50 --suggest-top-p 0.9

# Inspect current configuration
python -m zdownloadmanager.cli --show-config

# List available OpenRouter models
python -m zdownloadmanager.cli --list-models

# Print version
python -m zdownloadmanager.cli --version

# Scrape links from a page
python -m zdownloadmanager.cli --scrape https://httpbin.org/links/5/0

# Clear cached suggestions
python -m zdownloadmanager.cli --clear-suggestions-cache

# Show cached suggestions
python -m zdownloadmanager.cli --show-suggestions-cache

# Display context snapshot
python -m zdownloadmanager.cli --show-context-snapshot

# Display code snapshot
python -m zdownloadmanager.cli --show-code-snapshot

# Verify snapshots are current
python -m zdownloadmanager.cli --verify-snapshots

# Show dependencies for the CLI module
python -m zdownloadmanager.cli --show-dependencies ZDownloadManager/zdownloadmanager/cli.py

# Show modules that depend on the config module
python -m zdownloadmanager.cli --show-dependents ZDownloadManager/zdownloadmanager/core/config.py

# List library contents
python -m zdownloadmanager.cli --list-library

# Search library for files containing "foo"
python -m zdownloadmanager.cli --search-library foo

# Show counts per category and tag
python -m zdownloadmanager.cli --library-stats
```

## GitHub Automation
Use `scripts/github_tools.py` for basic repository automation. Set the
`GITHUB_TOKEN` environment variable to a personal access token with
repository permissions.

```bash
# Create or update a file
GITHUB_TOKEN=xxx python scripts/github_tools.py commit-file owner/repo path/to/file "message" "content"

# Open a pull request
GITHUB_TOKEN=xxx python scripts/github_tools.py create-pr owner/repo "Title" user:branch --body "description"

# List open issues
GITHUB_TOKEN=xxx python scripts/github_tools.py list-issues owner/repo --limit 5

# List open pull requests
GITHUB_TOKEN=xxx python scripts/github_tools.py list-prs owner/repo --limit 5

# Show repository languages
GITHUB_TOKEN=xxx python scripts/github_tools.py list-languages owner/repo
```

## Testing
Run the test suite:
```bash
python -m unittest discover ZDownloadManager/tests -v
```

See [`ZDownloadManager/README.md`](ZDownloadManager/README.md) for full details and packaging notes.

## Development
Run style and lint checks via [pre-commit](https://pre-commit.com/):
```bash
pre-commit run --all-files
```

When adding new features or refactoring, include tests and documentation to guide future agents.
The `Makefile` mirrors these commands with shortcuts (`make lint`, `make test`, `make context`, `make models`, `make check`). `make context` regenerates both context and code snapshots.

`make check` runs linting, compilation, context snapshot verification, CLI inspection and the unit test suite in one step.

The snapshot intentionally omits the most recent commit in its log so the `--check` verification remains stable after commits.

Current version: 0.1.29
