"""Smart file organizer and renamer.

This module normalises filenames, categorises them by type and moves them
into the user's library. It uses the configuration categories to determine
which folder a file belongs to. After moving, it updates the library index.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Dict, Optional, Tuple

from .config import Config


class Organizer:
    """Handle renaming and moving downloaded files into the library."""

    VERSION_RE = re.compile(r"(?<!\w)(\d+(?:\.\d+)+)")

    def __init__(self, config: Optional[Config] = None) -> None:
        self.config = config or Config()

    def normalize_filename(self, filename: str) -> str:
        """Return a cleaned version of the given filename.

        * Replace underscores and hyphens with spaces.
        * Collapse multiple consecutive spaces to a single space.
        * Insert a 'v' before version numbers if absent (e.g. `1.2.3` → `v1.2.3`).
        * Preserve the file extension.
        """
        path = Path(filename)
        name = path.stem
        ext = path.suffix
        # Replace underscores and hyphens with spaces
        name = re.sub(r"[\-_]+", " ", name)
        # Insert 'v' before version numbers not already prefixed by v
        def insert_v(match: re.Match[str]) -> str:
            ver = match.group(1)
            # If it already starts with v or V, return unchanged
            if name[: match.start()].lower().endswith("v"):
                return ver
            return f"v{ver}"
        name = self.VERSION_RE.sub(lambda m: insert_v(m), name)
        # Collapse multiple spaces
        name = re.sub(r"\s{2,}", " ", name).strip()
        return f"{name}{ext}"

    def determine_category(self, filename: str) -> Tuple[str, Dict[str, str]]:
        """Return the category key and metadata for the given filename.

        The category is determined by the file extension against
        ``Config.categories``. If no category matches, 'files' is returned.
        """
        ext = Path(filename).suffix.lower()
        cats = self.config.categories
        for cat_name, info in cats.items():
            exts = [e.lower() for e in info.get("extensions", [])]
            if ext in exts or (not exts and cat_name == "files"):
                return cat_name, info
        return "files", cats.get("files", {})

    def organise(self, path: Path) -> Path:
        """Rename and move the file into the library.

        Returns the new file path.
        """
        if not path.exists():
            raise FileNotFoundError(path)
        new_name = self.normalize_filename(path.name)
        category, cat_info = self.determine_category(new_name)
        # Choose the first library root as destination base
        lib_roots = self.config.library_roots
        if not lib_roots:
            dest_root = path.parent
        else:
            dest_root = Path(lib_roots[0])
        dest_dir = dest_root / category
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / new_name
        # If there's a collision, append a number
        counter = 1
        stem = dest_path.stem
        ext = dest_path.suffix
        while dest_path.exists():
            dest_path = dest_dir / f"{stem} ({counter}){ext}"
            counter += 1
        shutil.move(str(path), dest_path)
        return dest_path
