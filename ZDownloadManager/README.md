ZDownloadManager
=================

**Version 0.1.28**

ZDownloadManager is a cross‑platform download manager and smart file organizer designed to run on
Windows and macOS. It features:

* **Resumable downloads:** Download files from one or more mirrors. If the connection is
  interrupted the manager will use HTTP Range requests to resume from exactly where
  it left off. When Range support is unavailable, it falls back to a sequential
  streaming mode. This technique is part of the HTTP specification and allows
  partial content retrieval.
* **Byte‑level verification:** Each download is split into pieces and hashed
  using SHA‑256. When resuming, pieces are validated on disk and requeued if
  corrupt.
* **Multi‑source support:** Supply a list of mirror URLs separated by commas. If one
  server fails to deliver a piece the next mirror is tried automatically.
* **Library manager:** Once a download completes it is automatically
  organised into logical categories (programs, packages, other files) and indexed in
  a library. Categories and tags can be defined and adjusted by the user.
* **Smart renaming:** Filenames are normalised by replacing underscores and
  hyphens with spaces and heuristically inserting a `v`
  prefix before version numbers. This produces consistently readable names (for
  example `my-file-1.0.zip` becomes `my file v1.0.zip`).
* **Right‑click actions:** The library view exposes a configurable context menu.
  Actions are defined in a JSON file and can launch external programs, run
  scripts or display computed information. A built‑in editor allows editing
  the actions from within the application.
* **Chrome integration:** A native messaging host and a small MV3 extension
  allow Chrome/Chromium to hand off downloads to ZDownloadManager. To install
  the native host, run the appropriate script in `install/` and load the
  extension from `chrome_extension/`.
* **Comprehensive configuration:** An in‑app Config menu lets you adjust piece
  size, concurrency, library roots, context menu actions, suggestions and the
  OpenRouter API key.
* **LLM suggestions:** Query OpenRouter for contextual file information with
  on‑disk caching to avoid repeated requests.
* **Streamed suggestions:** `--suggest-stream` streams AI responses as they arrive.
* **Model selection:** Override the OpenRouter model with `--suggest-model` or
  via the configuration menu.
* **Parameter control:** Adjust `temperature`, `max_tokens` and `top_p` via `--suggest-temperature`, `--suggest-max-tokens` and `--suggest-top-p`.
* **CLI introspection:** `--version` prints the package version and
  `--show-config` dumps the active configuration.
* **Model listing:** `--list-models` fetches available OpenRouter models.
* **Web scraping:** `--scrape` prints links discovered on a web page.
* **Cache management:** `--clear-suggestions-cache` deletes stored AI responses.
* **Cache inspection:** `--show-suggestions-cache` prints stored AI responses.
* **GitHub automation:** `scripts/github_tools.py` can commit files, open pull requests, list issues, list pull requests, and display repository languages.
* **Code snapshotting:** `scripts/code_scan.py` summarises classes and functions across the project for agents.
* **Snapshot helpers:** `--show-context-snapshot`, `--show-code-snapshot` and `--verify-snapshots` expose snapshot data and checks.
* **Dependency mapping:** the context snapshot records Python import relationships so agents can see which files a change may impact.
* **Dependency queries:** `--show-dependencies` and `--show-dependents` reveal module relationships from the context snapshot.

Getting Started
---------------

From the repository root, run `./init.sh` to display project documentation, install all dependencies and pre-commit hooks. The script also writes `context_snapshot` and `code_snapshot` files; the context snapshot includes a dependency graph of Python imports. Alternatively, within this directory:

```bash
pip install -r requirements.txt

# Start the graphical application
python -m zdownloadmanager.ui.main_window

# Or use the CLI
zdm https://example.com/file.iso -o /path/to/file.iso --mirrors https://mirror1.com/file.iso,https://mirror2.com/file.iso

# Ask the AI a question
zdm --suggest "What is this project?"
# Use a specific model
zdm --suggest "What is this project?" --suggest-model openai/gpt-4o-mini
# Stream the response
zdm --suggest-stream "What is this project?"
# Tune suggestion parameters
zdm --suggest "What is this project?" --suggest-temperature 0.5 --suggest-max-tokens 50 --suggest-top-p 0.9

# List links from a page
zdm --scrape https://httpbin.org/links/5/0

# List available OpenRouter models
zdm --list-models

# Clear cached suggestions
zdm --clear-suggestions-cache

# Show cached suggestions
zdm --show-suggestions-cache

# Display context snapshot
zdm --show-context-snapshot

# Display code snapshot
zdm --show-code-snapshot

# Verify snapshots are current
zdm --verify-snapshots

# Show dependencies for the CLI module
zdm --show-dependencies ZDownloadManager/zdownloadmanager/cli.py

# Show modules that depend on the config module
zdm --show-dependents ZDownloadManager/zdownloadmanager/core/config.py

# List library contents
zdm --list-library

# Search library for files containing "foo"
zdm --search-library foo

# Show counts per category and tag
zdm --library-stats
```

GitHub Automation
-----------------

Basic GitHub interactions are available via `scripts/github_tools.py`.
Set `GITHUB_TOKEN` to a personal access token with repository scope.

```bash
# Commit a file
GITHUB_TOKEN=xxx python ../scripts/github_tools.py commit-file owner/repo path "message" "content"

# Open a pull request
GITHUB_TOKEN=xxx python ../scripts/github_tools.py create-pr owner/repo "Title" user:branch --body "description"

# List open issues
GITHUB_TOKEN=xxx python ../scripts/github_tools.py list-issues owner/repo --limit 5

# List open pull requests
GITHUB_TOKEN=xxx python ../scripts/github_tools.py list-prs owner/repo --limit 5

# Show repository languages
GITHUB_TOKEN=xxx python ../scripts/github_tools.py list-languages owner/repo
```

The first time you run the GUI, a configuration directory is created in a
platform‑appropriate location. You can customise library roots, piece size,
concurrency, categories, actions, suggestion preferences and the OpenRouter
API key via the **Config** menu.

Testing
-------

Run the unit test suite with:

```bash
python -m unittest discover tests -v
```

Packaging & Distribution
------------------------

To produce a stand‑alone build for Windows or macOS you can use
PyInstaller. The project intentionally avoids external native dependencies to
ease packaging. Building the installer is left to distribution tools like
Inno Setup (Windows) or a macOS `pkg`. The `chrome_extension/` directory
contains an example MV3 extension and the `install/` folder has scripts to
install the native messaging host. See their individual readme comments for
details.

Development
-----------

Run code style checks with [pre-commit](https://pre-commit.com/):

```bash
pre-commit run --all-files
```

The repository provides a `Makefile` with shortcuts for common tasks:

```bash
make lint     # run pre-commit hooks
make test     # run unit tests
make context  # regenerate context and code snapshots
make models   # list available OpenRouter models
make check    # run linting, context snapshot check, compilation, CLI help and tests
```

When adding new features or refactoring, update the documentation and tests so future agents understand the changes.


License
-------

This software is distributed as free software. Feel free to modify and
redistribute it under the terms of the MIT license.
