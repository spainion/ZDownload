import json
import os
import subprocess
import sys
from pathlib import Path

from zdownloadmanager.core.config import Config
from zdownloadmanager.core.library import Library


def setup_home(tmp_path: Path) -> tuple[Path, Path, Config]:
    """Create a fake HOME with a library and config."""
    home = tmp_path / "home"
    lib_dir = home / "library"
    cfg_path = home / ".config" / "zdownloadmanager" / "config.json"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    lib_dir.mkdir(parents=True, exist_ok=True)
    cfg = Config(cfg_path)
    cfg.update(library_roots=[str(lib_dir)])
    return home, lib_dir, cfg


def test_library_scan_and_search(tmp_path: Path) -> None:
    home, lib_dir, cfg = setup_home(tmp_path)
    file_path = lib_dir / "example.txt"
    file_path.write_text("data", encoding="utf-8")
    lib = Library(cfg)
    items = lib.scan()
    assert any(p == str(file_path) for p, _c, _t in items)
    results = lib.search("exam")
    assert results == [(str(file_path), "files", [])]


def test_cli_list_and_search(tmp_path: Path) -> None:
    home, lib_dir, _cfg = setup_home(tmp_path)
    (lib_dir / "foo.txt").write_text("data", encoding="utf-8")
    env = os.environ.copy()
    env["HOME"] = str(home)
    out = subprocess.check_output(
        [sys.executable, "-m", "zdownloadmanager.cli", "--list-library"],
        text=True,
        env=env,
    )
    assert "foo.txt (files)" in out
    out = subprocess.check_output(
        [
            sys.executable,
            "-m",
            "zdownloadmanager.cli",
            "--search-library",
            "foo",
        ],
        text=True,
        env=env,
    )
    assert "foo.txt (files)" in out


def test_cli_library_stats(tmp_path: Path) -> None:
    home, lib_dir, _cfg = setup_home(tmp_path)
    (lib_dir / "a.txt").write_text("x", encoding="utf-8")
    (lib_dir / "b.txt").write_text("y", encoding="utf-8")
    env = os.environ.copy()
    env["HOME"] = str(home)
    out = subprocess.check_output(
        [sys.executable, "-m", "zdownloadmanager.cli", "--library-stats"],
        text=True,
        env=env,
    )
    data = json.loads(out)
    assert data["categories"]["files"] == 2
