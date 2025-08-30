"""Library index and search support.

The Library class maintains an index of files organised by ZDownloadManager.
It can scan configured library roots, determine categories and manage tags.
Tags are stored in a JSON file in the configuration directory alongside the
main configuration file.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from .config import Config
from .organizer import Organizer


class Library:
    def __init__(self, config: Optional[Config] = None) -> None:
        self.config = config or Config()
        self.organizer = Organizer(self.config)
        self.tags_path = Path(self.config.path).with_name("tags.json")
        self.tags: Dict[str, List[str]] = {}
        self._load_tags()

    def _load_tags(self) -> None:
        if self.tags_path.exists():
            try:
                with self.tags_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.tags = {k: list(v) for k, v in data.items()}
            except (OSError, json.JSONDecodeError):
                self.tags = {}
        else:
            self.tags = {}

    def _save_tags(self) -> None:
        tmp = self.tags_path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(self.tags, f, indent=2)
        tmp.replace(self.tags_path)

    def scan(self) -> List[Tuple[str, str, List[str]]]:
        """Scan library roots and return a list of (path, category, tags)."""
        items: List[Tuple[str, str, List[str]]] = []
        for root in self.config.library_roots:
            base = Path(root)
            if not base.exists():
                continue
            for path in base.rglob("*"):
                if path.is_file():
                    category, _info = self.organizer.determine_category(path.name)
                    tags = self.tags.get(str(path), [])
                    items.append((str(path), category, tags))
        return items

    def search(self, query: str) -> List[Tuple[str, str, List[str]]]:
        """Search by filename or tags (case‑insensitive)."""
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        results = []
        for path, category, tags in self.scan():
            if pattern.search(Path(path).name) or any(pattern.search(t) for t in tags):
                results.append((path, category, tags))
        return results

    def stats(self) -> Dict[str, Dict[str, int]]:
        """Return counts of files per category and tag."""
        category_counts: Dict[str, int] = {}
        tag_counts: Dict[str, int] = {}
        for _path, category, tags in self.scan():
            category_counts[category] = category_counts.get(category, 0) + 1
            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        return {"categories": category_counts, "tags": tag_counts}

    def set_tags(self, path: str, tags: Iterable[str]) -> None:
        self.tags[str(path)] = list(tags)
        self._save_tags()

    def add_tag(self, path: str, tag: str) -> None:
        tags = set(self.tags.get(str(path), []))
        tags.add(tag)
        self.tags[str(path)] = list(tags)
        self._save_tags()

    def remove_tag(self, path: str, tag: str) -> None:
        tags = set(self.tags.get(str(path), []))
        if tag in tags:
            tags.remove(tag)
            if tags:
                self.tags[str(path)] = list(tags)
            else:
                self.tags.pop(str(path), None)
            self._save_tags()
