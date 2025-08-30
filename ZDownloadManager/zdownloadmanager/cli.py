"""Command line interface for ZDownloadManager.

This script provides a basic CLI for downloading files using the segmented
downloader and then organising them into the library. It accepts a primary
URL and an optional comma‑separated list of mirrors. It can be used as a
simple default download handler or invoked by the Chrome bridge.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

from . import __version__
from .core.config import Config
from .core.downloader import SegmentedDownloader, DownloadError
from .core.organizer import Organizer


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Download files with resume and organise them.")
    parser.add_argument("url", nargs="?", default="", help="Primary download URL")
    parser.add_argument("-o", "--output", dest="output", default=None, help="Destination file path")
    parser.add_argument("--mirrors", dest="mirrors", default="", help="Comma separated list of mirror URLs")
    parser.add_argument("--piece", dest="piece_size", type=int, default=None, help="Piece size in bytes (default 4 MiB)")
    parser.add_argument("--conc", dest="concurrency", type=int, default=None, help="Number of concurrent pieces (default 4)")
    parser.add_argument("--suggest", dest="suggest", default=None, help="Ask the AI about a question instead of downloading")
    parser.add_argument(
        "--suggest-stream",
        dest="suggest_stream",
        default=None,
        help="Stream an AI answer for a question",
    )
    parser.add_argument("--suggest-model", dest="suggest_model", default=None, help="Model to use with --suggest")
    parser.add_argument(
        "--suggest-temperature",
        dest="suggest_temperature",
        type=float,
        default=None,
        help="Temperature for AI suggestions",
    )
    parser.add_argument(
        "--suggest-max-tokens",
        dest="suggest_max_tokens",
        type=int,
        default=None,
        help="Max tokens for AI suggestions",
    )
    parser.add_argument(
        "--suggest-top-p",
        dest="suggest_top_p",
        type=float,
        default=None,
        help="Top-p nucleus sampling for AI suggestions",
    )
    parser.add_argument("--scrape", dest="scrape", default=None, help="Fetch a page and list links")
    parser.add_argument("--list-library", action="store_true", help="List indexed library files and exit")
    parser.add_argument("--search-library", dest="search_library", default=None, help="Search library files and exit")
    parser.add_argument("--library-stats", action="store_true", help="Show library statistics and exit")
    parser.add_argument("--version", action="store_true", help="Print version and exit")
    parser.add_argument("--show-config", action="store_true", help="Display configuration and exit")
    parser.add_argument("--list-models", action="store_true", help="List OpenRouter models and exit")
    parser.add_argument(
        "--clear-suggestions-cache",
        action="store_true",
        help="Delete cached suggestions and exit",
    )
    parser.add_argument(
        "--show-suggestions-cache",
        action="store_true",
        help="Print cached suggestions and exit",
    )
    parser.add_argument(
        "--show-context-snapshot",
        action="store_true",
        help="Print context snapshot and exit",
    )
    parser.add_argument(
        "--show-code-snapshot",
        action="store_true",
        help="Print code snapshot and exit",
    )
    parser.add_argument(
        "--verify-snapshots",
        action="store_true",
        help="Verify context and code snapshots are up to date and exit",
    )
    parser.add_argument(
        "--show-dependencies",
        dest="show_dependencies",
        default=None,
        help="Show imports for a module from context snapshot and exit",
    )
    parser.add_argument(
        "--show-dependents",
        dest="show_dependents",
        default=None,
        help="Show modules that import the given module from context snapshot and exit",
    )
    args = parser.parse_args(argv)

    if args.version:
        print(__version__)
        return

    cfg = Config()
    if args.show_config:
        print(json.dumps(cfg.data, indent=2))
        return
    if args.list_models:
        root = Path(__file__).resolve().parents[2]
        script = root / "scripts" / "openrouter_models.py"
        out = subprocess.check_output([sys.executable, str(script)], cwd=root, text=True)
        print(out)
        return
    if args.show_context_snapshot:
        root = Path(__file__).resolve().parents[2]
        print((root / "context_snapshot.md").read_text(encoding="utf-8"))
        return
    if args.show_code_snapshot:
        root = Path(__file__).resolve().parents[2]
        print((root / "code_snapshot.md").read_text(encoding="utf-8"))
        return
    if args.verify_snapshots:
        root = Path(__file__).resolve().parents[2]
        scripts = root / "scripts"
        subprocess.check_call([sys.executable, str(scripts / "context_snapshot.py"), "--check"], cwd=root)
        subprocess.check_call([sys.executable, str(scripts / "code_scan.py"), "--check"], cwd=root)
        print("Snapshots up to date")
        return
    if args.show_dependencies or args.show_dependents:
        root = Path(__file__).resolve().parents[2]
        data = json.loads((root / "context_snapshot.json").read_text(encoding="utf-8")).get("dependencies", {})
        if args.show_dependencies:
            key = Path(args.show_dependencies).as_posix()
            for dep in data.get(key, []):
                print(dep)
            return
        if args.show_dependents:
            key = Path(args.show_dependents).as_posix()
            for mod, deps in data.items():
                if key in deps:
                    print(mod)
            return
    if args.clear_suggestions_cache:
        from .core.suggestions import clear_cache

        if clear_cache(cfg):
            print("Suggestion cache cleared")
        else:
            print("No suggestion cache present")
        return
    if args.show_suggestions_cache:
        from .core.suggestions import read_cache

        cache = read_cache(cfg)
        if cache:
            print(json.dumps(cache, indent=2))
        else:
            print("No suggestion cache present")
        return
    if args.list_library or args.search_library or args.library_stats:
        from .core.library import Library

        lib = Library(cfg)
        if args.library_stats:
            print(json.dumps(lib.stats(), indent=2))
        else:
            items = lib.search(args.search_library) if args.search_library else lib.scan()
            for path, category, tags in items:
                tag_str = f" [{', '.join(tags)}]" if tags else ""
                print(f"{path} ({category}){tag_str}")
        return
    if args.suggest_stream:
        from .core.suggestions import stream_suggestion

        updates = {}
        if args.suggest_model:
            updates["openrouter_model"] = args.suggest_model
        if args.suggest_temperature is not None:
            updates["openrouter_temperature"] = args.suggest_temperature
        if args.suggest_max_tokens is not None:
            updates["openrouter_max_tokens"] = args.suggest_max_tokens
        if args.suggest_top_p is not None:
            updates["openrouter_top_p"] = args.suggest_top_p
        if updates:
            cfg.update(**updates)
        gen = stream_suggestion(
            cfg,
            args.suggest_stream,
            model=args.suggest_model,
        )
        if gen is None:
            print("No suggestion available")
        else:
            for part in gen:
                print(part, end="", flush=True)
            print()
        return
    if args.suggest:
        from .core.suggestions import get_suggestion

        updates = {}
        if args.suggest_model:
            updates["openrouter_model"] = args.suggest_model
        if args.suggest_temperature is not None:
            updates["openrouter_temperature"] = args.suggest_temperature
        if args.suggest_max_tokens is not None:
            updates["openrouter_max_tokens"] = args.suggest_max_tokens
        if args.suggest_top_p is not None:
            updates["openrouter_top_p"] = args.suggest_top_p
        if updates:
            cfg.update(**updates)
        answer = get_suggestion(
            cfg,
            args.suggest,
            model=args.suggest_model,
        )
        if answer:
            print(answer)
        else:
            print("No suggestion available")
        return
    if args.scrape:
        from .core.webscraper import scrape_links

        links = scrape_links(args.scrape)
        for link in links:
            print(link)
        return
    if not args.url:
        parser.error("url required when not using --suggest, --suggest-stream or --scrape")
    urls = [args.url] + [u for u in args.mirrors.split(",") if u.strip()]
    dest = Path(args.output) if args.output else Path(Path(args.url).name)
    piece_size = args.piece_size or cfg.piece_size
    concurrency = args.concurrency or cfg.concurrency
    try:
        dl = SegmentedDownloader(urls, dest, piece_size=piece_size, concurrency=concurrency)
        dl.download()
    except DownloadError as e:
        print(f"Download failed: {e}")
        return
    # Before organising the downloaded file into the library, verify that the
    # file has been completely downloaded. This helps avoid moving partial
    # downloads into the library (which can happen if the process was killed
    # mid‑download). We check the expected file size stored in the manifest
    # against the actual size on disk.
    expected_size = None
    try:
        # dl.conn may be closed at this point, so re‑open to fetch meta
        expected_size_str = dl._get_meta("file_size") if hasattr(dl, '_get_meta') else None
        if expected_size_str and expected_size_str.isdigit():
            expected_size = int(expected_size_str)
    except Exception:
        expected_size = None
    try:
        actual_size = dest.stat().st_size
    except Exception:
        actual_size = None
    # If we know the expected size and the file on disk is smaller, skip
    # organisation and inform the user.
    if expected_size is not None and actual_size is not None and actual_size < expected_size:
        print(
            f"Download incomplete: expected {expected_size} bytes, got {actual_size} bytes. "
            f"File remains at {dest}."
        )
        return
    # Organise into library
    organizer = Organizer(cfg)
    try:
        new_path = organizer.organise(dest)
        print(f"Downloaded and stored at: {new_path}")
    except Exception as e:
        # If organisation fails, report and leave the file where it is
        print(f"Failed to organise file: {e}")
        print(f"File remains at: {dest}")


if __name__ == "__main__":
    main()
