"""Configuration management for ZDownloadManager.

This module handles reading and writing a user configuration file stored in the
platform‑specific application data directory. The configuration includes
download preferences, library roots, category definitions, tags, and custom
actions for the context menu.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

from .. import __version__


def _platform_config_dir() -> Path:
    r"""Return the path to the configuration directory for the current OS.

    On Windows, use %APPDATA%\ZDownloadManager, on macOS use
    ~/Library/Application Support/ZDownloadManager, on other systems use
    ~/.config/zdownloadmanager.
    """
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return base / "ZDownloadManager"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "ZDownloadManager"
    else:
        return Path.home() / ".config" / "zdownloadmanager"


class Config:
    """Represents the user configuration and provides persistence helpers."""

    DEFAULT_CATEGORIES = {
        "programs": {
            "extensions": [".exe", ".msi", ".app", ".dmg", ".pkg", ".sh", ".bat"],
            "tags": ["executable", "application"],
        },
        "packages": {
            "extensions": [".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar", ".whl", ".deb", ".rpm"],
            "tags": ["archive", "package"],
        },
        "files": {
            "extensions": [],
            "tags": ["file"],
        },
    }

    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path or (_platform_config_dir() / "config.json")
        self.data: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load configuration from disk, merging with defaults if necessary."""
        config_dir = self.path.parent
        config_dir.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            try:
                with self.path.open("r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except (json.JSONDecodeError, OSError):
                # Start fresh if the file is corrupt
                self.data = {}
        else:
            self.data = {}

        # Populate missing fields
        self.data.setdefault("piece_size", 4 * 1024 * 1024)  # 4 MiB
        self.data.setdefault("concurrency", 4)
        self.data.setdefault("library_roots", [str(Path.home() / "Downloads")])
        self.data.setdefault("categories", self.DEFAULT_CATEGORIES)
        self.data.setdefault("actions", {
            "Open": {"cmd": "open {path}", "platform": ["darwin"]},
            "Reveal": {"cmd": "xdg-open {dir}", "platform": ["linux"]},
            "Sha256": {
                "cmd": "python - <<'PY'\nimport hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())\nPY {path}",
                "platform": ["any"],
            },
        })
        # Custom openers allow mapping file extensions to a specific program
        self.data.setdefault("custom_openers", {})
        # Flag to enable or disable suggestions from OpenRouter
        self.data.setdefault("suggestions_enabled", False)
        # API key for OpenRouter; load from environment if not present
        env_key = os.environ.get("OPENROUTER_API_KEY")
        if env_key and not self.data.get("openrouter_api_key"):
            self.data["openrouter_api_key"] = env_key
        self.data.setdefault("openrouter_api_key", "")
        # Default OpenRouter model and parameters
        self.data.setdefault("openrouter_model", "openai/gpt-4o")
        self.data.setdefault("openrouter_temperature", 1.0)
        self.data.setdefault("openrouter_max_tokens", 256)
        self.data.setdefault("openrouter_top_p", 1.0)
        # Track last known package version
        self.data.setdefault("last_version", __version__)
        if self.data["last_version"] != __version__:
            self.data["last_version"] = __version__
            self.save()

    def save(self) -> None:
        """Write configuration back to disk."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path.with_suffix(".tmp")
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)
        tmp_path.replace(self.path)

    # Properties for convenience
    @property
    def piece_size(self) -> int:
        return int(self.data.get("piece_size", 4 * 1024 * 1024))

    @property
    def concurrency(self) -> int:
        return int(self.data.get("concurrency", 4))

    @property
    def library_roots(self) -> List[str]:
        return list(self.data.get("library_roots", []))

    @property
    def categories(self) -> Dict[str, Dict[str, Any]]:
        return self.data.get("categories", self.DEFAULT_CATEGORIES)

    @property
    def actions(self) -> Dict[str, Dict[str, Any]]:
        return self.data.get("actions", {})

    @property
    def custom_openers(self) -> Dict[str, str]:
        return self.data.get("custom_openers", {})

    @property
    def suggestions_enabled(self) -> bool:
        return bool(self.data.get("suggestions_enabled", False))

    @property
    def openrouter_api_key(self) -> str:
        return self.data.get("openrouter_api_key", "")

    @property
    def openrouter_model(self) -> str:
        return self.data.get("openrouter_model", "openai/gpt-4o")

    @property
    def openrouter_temperature(self) -> float:
        return float(self.data.get("openrouter_temperature", 1.0))

    @property
    def openrouter_max_tokens(self) -> int:
        return int(self.data.get("openrouter_max_tokens", 256))

    @property
    def openrouter_top_p(self) -> float:
        return float(self.data.get("openrouter_top_p", 1.0))

    @property
    def last_version(self) -> str:
        return self.data.get("last_version", "")

    @property
    def cache_dir(self) -> Path:
        """Directory for auxiliary cached data."""
        return self.path.parent

    def update(self, **kwargs: Any) -> None:
        """Update configuration values and save to disk."""
        self.data.update(kwargs)
        self.save()
