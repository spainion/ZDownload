# File: AGENTS.md

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

# File: README.md

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

# File: ZDownloadManager/README.md

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

# File: ZDownloadManager/install/macos_quick_action.md

## macOS Quick Action for ZDownloadManager

To add a Finder Quick Action that sends files to ZDownloadManager:

1. Open **Automator** and create a new **Quick Action**.
2. Set **Workflow receives current** to *files or folders* in *Finder*.
3. From the **Actions** library search for **Run Shell Script** and drag it to the workflow.
4. Set **Shell** to `/bin/bash` and **Pass input** to `as arguments`.
5. Replace the script body with:

   ```bash
   for f in "$@"; do
       python3 -m zdownloadmanager.cli "$f"
   done
   ```

6. Save the Quick Action with a name like **Send to ZDownloadManager**.

After saving, right‑click any file in Finder and choose **Quick Actions → Send to ZDownloadManager** to organise it via the command line.

# File: code_snapshot.md

# Code Snapshot

## ZDownloadManager/tests/__init__.py

## ZDownloadManager/tests/test_cli.py
- class CLITests
  - test_version_flag(self)
  - test_show_config(self)
  - test_show_snapshots(self)
  - test_verify_snapshots(self)
  - test_list_models(self)
  - test_dependency_queries(self)

## ZDownloadManager/tests/test_code_scanner.py
- test_code_scanner_generates_summary(tmp_path)

## ZDownloadManager/tests/test_config.py
- class ConfigTests
  - test_update_and_reload(self)

## ZDownloadManager/tests/test_context_snapshot.py
- class ContextSnapshotTest
  - test_snapshot_created(self)

## ZDownloadManager/tests/test_downloader.py
- class DownloaderTests
  - test_download_example(self)

## ZDownloadManager/tests/test_github_adapter.py
- class GitHubAdapterTests
  - test_get_repo_info(self)
  - test_list_open_issues(self)
  - test_list_open_pull_requests(self)
  - test_list_languages(self)

## ZDownloadManager/tests/test_library_cli.py
- setup_home(tmp_path)
- test_library_scan_and_search(tmp_path)
- test_cli_list_and_search(tmp_path)
- test_cli_library_stats(tmp_path)

## ZDownloadManager/tests/test_openrouter_models.py
- class OpenRouterModelsTest
  - test_models_fetch(self)

## ZDownloadManager/tests/test_organizer.py
- class OrganizerTests
  - test_normalize_filename(self)

## ZDownloadManager/tests/test_suggestions_cache.py
- class SuggestionCacheTest
  - test_cache_reuse_without_key(self)
  - test_cli_show_cache(self)
  - test_custom_model(self)
  - test_cli_custom_model(self)
  - test_cli_custom_params(self)
  - test_streaming(self)
  - test_cli_stream(self)

## ZDownloadManager/tests/test_webscraper.py
- class WebScraperTests
  - test_example_com(self)

## ZDownloadManager/zdownloadmanager/__init__.py

## ZDownloadManager/zdownloadmanager/cli.py
- main(argv)

## ZDownloadManager/zdownloadmanager/core/config.py
- _platform_config_dir()
- class Config
  - __init__(self, path)
  - load(self)
  - save(self)
  - piece_size(self)
  - concurrency(self)
  - library_roots(self)
  - categories(self)
  - actions(self)
  - custom_openers(self)
  - suggestions_enabled(self)
  - openrouter_api_key(self)
  - openrouter_model(self)
  - openrouter_temperature(self)
  - openrouter_max_tokens(self)
  - openrouter_top_p(self)
  - last_version(self)
  - cache_dir(self)
  - update(self, **kwargs)

## ZDownloadManager/zdownloadmanager/core/downloader.py
- class Piece
- class DownloadError
- class SegmentedDownloader
  - __init__(self, urls, dest, piece_size, concurrency, timeout, user_agent)
  - _init_db(self)
  - _get_meta(self, key)
  - _set_meta(self, key, value)
  - _enumerate_pieces(self, file_size)
  - _load_pieces(self)
  - _save_piece(self, piece)
  - _probe_server(self, url)
  - download(self)
  - _sequential_download(self, file_size)

## ZDownloadManager/zdownloadmanager/core/github_adapter.py
- class GitHubAdapter
  - __init__(self, token)
  - get_repo_info(self, full_name)
  - commit_file(self, repo_full_name, path, content, message, branch)
  - create_pull_request(self, repo_full_name, title, body, head, base)
  - list_open_issues(self, repo_full_name, limit)
  - list_open_pull_requests(self, repo_full_name, limit)
  - list_languages(self, repo_full_name)

## ZDownloadManager/zdownloadmanager/core/library.py
- class Library
  - __init__(self, config)
  - _load_tags(self)
  - _save_tags(self)
  - scan(self)
  - search(self, query)
  - stats(self)
  - set_tags(self, path, tags)
  - add_tag(self, path, tag)
  - remove_tag(self, path, tag)

## ZDownloadManager/zdownloadmanager/core/organizer.py
- class Organizer
  - __init__(self, config)
  - normalize_filename(self, filename)
  - determine_category(self, filename)
  - organise(self, path)

## ZDownloadManager/zdownloadmanager/core/suggestions.py
- _cache_file(config)
- read_cache(config)
- clear_cache(config)
- get_suggestion(config, question, model)
- stream_suggestion(config, question, model)

## ZDownloadManager/zdownloadmanager/core/webscraper.py
- _get_session()
- scrape_page(url, headings, images, meta, summary, links, timeout)
- scrape_links(url, timeout)
- scrape_site(url, depth, headings, images, meta, summary, links, timeout, parallel, max_workers)
- class _SimpleHTMLParser
  - __init__(self)
  - handle_starttag(self, tag, attrs)
  - handle_endtag(self, tag)
  - handle_data(self, data)

## ZDownloadManager/zdownloadmanager/integration/native_messaging_host.py
- read_message()
- write_message(msg)
- main()

## ZDownloadManager/zdownloadmanager/integration/protocol_handler.py
- main(argv)

## ZDownloadManager/zdownloadmanager/ui/actions_editor.py
- class ActionsEditor
  - __init__(self, config, parent)
  - save(self)

## ZDownloadManager/zdownloadmanager/ui/main_window.py
- main()
- class DownloadWorker
  - __init__(self, urls, dest, cfg)
  - run(self)
- class MainWindow
  - __init__(self)
  - _setup_ui(self)
  - _setup_download_tab(self)
  - _setup_library_tab(self)
  - reload_config(self)
  - edit_actions(self)
  - set_piece_size(self)
  - set_concurrency(self)
  - toggle_suggestions(self, checked)
  - set_openrouter_api_key(self)
  - browse_dest(self)
  - add_download(self)
  - on_download_progress(self, item, done, total)
  - on_download_finished(self, item, new_path, error)
  - refresh_library(self)
  - on_tree_context_menu(self, pos)
  - on_tree_selection_changed(self)
  - open_file(self, path)
  - reveal_file(self, path)
  - add_tag_dialog(self, path)
  - run_action(self, path, cmd_template)
  - run_custom_opener(self, path, opener)
  - rename_file(self, path)
  - delete_file(self, path)
  - choose_library_root(self)

## scripts/code_scan.py
- format_args(args)
- scan_file(path)
- generate_summary(root)
- build_markdown(summary)
- main()

## scripts/context_snapshot.py
- build_dependency_map()
- generate_snapshot()
- main()

## scripts/github_tools.py
- main()

## scripts/llm_suggest.py
- main()

## scripts/openrouter_models.py
- main()

## Dependency graph

- ZDownloadManager/tests/__init__.py: []
- ZDownloadManager/tests/test_cli.py: []
- ZDownloadManager/tests/test_code_scanner.py: []
- ZDownloadManager/tests/test_config.py: []
- ZDownloadManager/tests/test_context_snapshot.py: []
- ZDownloadManager/tests/test_downloader.py: []
- ZDownloadManager/tests/test_github_adapter.py: []
- ZDownloadManager/tests/test_library_cli.py: []
- ZDownloadManager/tests/test_openrouter_models.py: []
- ZDownloadManager/tests/test_organizer.py: []
- ZDownloadManager/tests/test_suggestions_cache.py: []
- ZDownloadManager/tests/test_webscraper.py: []
- ZDownloadManager/zdownloadmanager/__init__.py: []
- ZDownloadManager/zdownloadmanager/cli.py: ZDownloadManager/zdownloadmanager/core/config.py, ZDownloadManager/zdownloadmanager/core/downloader.py, ZDownloadManager/zdownloadmanager/core/library.py, ZDownloadManager/zdownloadmanager/core/organizer.py, ZDownloadManager/zdownloadmanager/core/suggestions.py, ZDownloadManager/zdownloadmanager/core/webscraper.py
- ZDownloadManager/zdownloadmanager/core/config.py: []
- ZDownloadManager/zdownloadmanager/core/downloader.py: []
- ZDownloadManager/zdownloadmanager/core/github_adapter.py: []
- ZDownloadManager/zdownloadmanager/core/library.py: ZDownloadManager/zdownloadmanager/core/config.py, ZDownloadManager/zdownloadmanager/core/organizer.py
- ZDownloadManager/zdownloadmanager/core/organizer.py: ZDownloadManager/zdownloadmanager/core/config.py
- ZDownloadManager/zdownloadmanager/core/suggestions.py: ZDownloadManager/zdownloadmanager/core/config.py
- ZDownloadManager/zdownloadmanager/core/webscraper.py: ZDownloadManager/zdownloadmanager/core/config.py
- ZDownloadManager/zdownloadmanager/integration/native_messaging_host.py: ZDownloadManager/zdownloadmanager/cli.py
- ZDownloadManager/zdownloadmanager/integration/protocol_handler.py: ZDownloadManager/zdownloadmanager/cli.py
- ZDownloadManager/zdownloadmanager/ui/actions_editor.py: ZDownloadManager/zdownloadmanager/core/config.py
- ZDownloadManager/zdownloadmanager/ui/main_window.py: ZDownloadManager/zdownloadmanager/core/config.py, ZDownloadManager/zdownloadmanager/core/downloader.py, ZDownloadManager/zdownloadmanager/core/library.py, ZDownloadManager/zdownloadmanager/core/organizer.py, ZDownloadManager/zdownloadmanager/core/suggestions.py, ZDownloadManager/zdownloadmanager/ui/actions_editor.py
- scripts/code_scan.py: []
- scripts/context_snapshot.py: []
- scripts/github_tools.py: []
- scripts/llm_suggest.py: []
- scripts/openrouter_models.py: []

## Recent commits

461b6a6 Add files via upload
7e32e69 Merge pull request #1 from spainion/codex/extract-files-and-update-documentation
d34b9e7 feat: query dependencies from CLI
39e730b Add files via upload
a300fa5 Initial commit

## Repository status

 M context_snapshot.json
 M context_snapshot.md
?? ZDownloadManager/tests/__pycache__/
?? ZDownloadManager/zdownloadmanager/__pycache__/
?? ZDownloadManager/zdownloadmanager/core/__pycache__/
?? ZDownloadManager/zdownloadmanager/integration/__pycache__/
?? ZDownloadManager/zdownloadmanager/ui/__pycache__/

