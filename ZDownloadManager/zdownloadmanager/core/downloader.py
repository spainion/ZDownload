"""Resumable multi‑source downloader.

This module implements segmented downloads using HTTP Range requests. Each
download is broken into fixed‑size pieces. Metadata about each piece is
persisted to a SQLite database (``.zdm.db``) located adjacent to the final
destination file. During resume operations the manifest is read back and
completed pieces are verified with SHA‑256 before being skipped.

If the remote server does not advertise support for the Range header the
downloader falls back to a sequential streaming mode. In that case the
manifest simply records progress and resumes by restarting the download at
the last byte written.
"""
from __future__ import annotations

import hashlib
import os
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import requests


@dataclass
class Piece:
    """Represents a single piece of a segmented download."""

    idx: int
    start: int
    end: int
    sha256: Optional[str] = None
    status: str = "pending"  # pending, downloading, done
    last_url: Optional[str] = None


class DownloadError(Exception):
    pass


class SegmentedDownloader:
    """Download files from multiple mirrors with resume support."""

    def __init__(
        self,
        urls: Iterable[str],
        dest: Path,
        piece_size: int = 4 * 1024 * 1024,
        concurrency: int = 4,
        timeout: float = 15.0,
        user_agent: str = "ZDownloadManager/0.1",
    ) -> None:
        self.urls = [url.strip() for url in urls if url.strip()]
        if not self.urls:
            raise ValueError("At least one URL must be provided")
        self.dest = Path(dest)
        self.piece_size = piece_size
        self.concurrency = concurrency
        self.timeout = timeout
        self.user_agent = user_agent
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})
        self._lock = threading.Lock()
        # Manifest path
        self.manifest_path = self.dest.with_suffix(self.dest.suffix + ".zdm.db")
        # Allow the SQLite connection to be used from worker threads
        self.conn = sqlite3.connect(str(self.manifest_path), check_same_thread=False)
        self._init_db()

    def _init_db(self) -> None:
        """Create tables if they don't exist."""
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS pieces (
                idx INTEGER PRIMARY KEY,
                start INTEGER,
                end INTEGER,
                sha256 TEXT,
                status TEXT,
                last_url TEXT
            );
            """
        )
        self.conn.commit()

    def _get_meta(self, key: str) -> Optional[str]:
        cur = self.conn.cursor()
        cur.execute("SELECT value FROM meta WHERE key=?", (key,))
        row = cur.fetchone()
        return row[0] if row else None

    def _set_meta(self, key: str, value: str) -> None:
        cur = self.conn.cursor()
        cur.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)", (key, value))
        self.conn.commit()

    def _enumerate_pieces(self, file_size: int) -> List[Piece]:
        count = (file_size + self.piece_size - 1) // self.piece_size
        pieces = []
        for idx in range(count):
            start = idx * self.piece_size
            end = min(start + self.piece_size, file_size) - 1
            pieces.append(Piece(idx=idx, start=start, end=end))
        return pieces

    def _load_pieces(self) -> List[Piece]:
        cur = self.conn.cursor()
        cur.execute("SELECT idx, start, end, sha256, status, last_url FROM pieces ORDER BY idx")
        rows = cur.fetchall()
        return [Piece(*row) for row in rows]

    def _save_piece(self, piece: Piece) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO pieces (idx, start, end, sha256, status, last_url) VALUES (?, ?, ?, ?, ?, ?)",
            (piece.idx, piece.start, piece.end, piece.sha256, piece.status, piece.last_url),
        )
        self.conn.commit()

    def _probe_server(self, url: str) -> Tuple[int, bool]:
        """Return (file_size, range_supported)."""
        try:
            resp = self.session.head(url, timeout=self.timeout, allow_redirects=True)
            if resp.status_code >= 400:
                # Use GET for HEAD fallback
                resp = self.session.get(url, stream=True, timeout=self.timeout)
        except Exception:
            return (0, False)
        # Determine size
        length = resp.headers.get("Content-Length")
        file_size = int(length) if length and length.isdigit() else 0
        # Determine Range support
        range_supported = False
        accept_ranges = resp.headers.get("Accept-Ranges")
        if accept_ranges and accept_ranges.lower() == "bytes":
            range_supported = True
        else:
            # Try Range request with small range
            try:
                r = self.session.get(url, headers={"Range": "bytes=0-0"}, timeout=self.timeout, stream=True)
                if r.status_code == 206:
                    range_supported = True
            except Exception:
                pass
        return (file_size, range_supported)

    def download(self) -> None:
        """Perform the download, resuming if possible."""
        # Determine file size and range support using the first mirror
        file_size, range_supported = self._probe_server(self.urls[0])
        if file_size == 0:
            raise DownloadError("Unable to determine remote file size")
        # Save file size in manifest
        self._set_meta("file_size", str(file_size))
        self._set_meta("range_supported", "1" if range_supported else "0")
        # Ensure destination directory exists
        self.dest.parent.mkdir(parents=True, exist_ok=True)
        if range_supported:
            # Only preallocate the destination file when Range downloads are supported.
            # Preallocating for sequential downloads would result in a file full of zero
            # bytes followed by the streamed content appended, effectively doubling
            # the file size on resume. For sequential fallback we simply grow the
            # file as data arrives.
            if not self.dest.exists() or os.path.getsize(self.dest) != file_size:
                with open(self.dest, "wb") as f:
                    f.truncate(file_size)
        else:
            # For sequential fallback, ensure an empty file exists for future writes and
            # verification routines. If the file exists with a larger size (possibly
            # from a previous incorrect preallocation), truncate it to zero.
            if self.dest.exists():
                if os.path.getsize(self.dest) > file_size:
                    with open(self.dest, "wb"):
                        pass
            else:
                # Create an empty file
                with open(self.dest, "wb"):
                    pass
        pieces: List[Piece]
        # Load or create piece metadata
        if self._get_meta("initialised"):
            pieces = self._load_pieces()
        else:
            pieces = self._enumerate_pieces(file_size)
            for piece in pieces:
                self._save_piece(piece)
            self._set_meta("initialised", "1")
        # Verify completed pieces
        with open(self.dest, "rb+") as f:
            for piece in pieces:
                if piece.status == "done" and piece.sha256:
                    f.seek(piece.start)
                    data = f.read(piece.end - piece.start + 1)
                    digest = hashlib.sha256(data).hexdigest()
                    if digest != piece.sha256:
                        piece.status = "pending"
                        piece.sha256 = None
                        self._save_piece(piece)

        # Determine pending pieces
        pending = [p for p in pieces if p.status != "done"]
        if not pending:
            return  # Already completed
        if not range_supported:
            # Sequential fallback
            self._sequential_download(file_size)
            return
        # Use thread pool to download pending pieces
        progress_lock = threading.Lock()
        completed_count = 0
        total = len(pending)

        def worker(piece: Piece) -> None:
            nonlocal completed_count
            for url in self.urls:
                # Range header inclusive
                headers = {"Range": f"bytes={piece.start}-{piece.end}"}
                try:
                    with self.session.get(url, headers=headers, stream=True, timeout=self.timeout) as resp:
                        if resp.status_code not in (206, 200):
                            continue
                        data = resp.content
                        sha = hashlib.sha256(data).hexdigest()
                        with self._lock:
                            with open(self.dest, "rb+") as f:
                                f.seek(piece.start)
                                f.write(data)
                        piece.sha256 = sha
                        piece.status = "done"
                        piece.last_url = url
                        self._save_piece(piece)
                        break
                except Exception:
                    continue
            else:
                raise DownloadError(f"Failed to download piece {piece.idx}")
            with progress_lock:
                completed_count += 1
                # Simple progress indicator on stderr
                print(f"\rDownloaded {completed_count}/{total} pieces", end="")

        with ThreadPoolExecutor(max_workers=self.concurrency) as pool:
            futures = [pool.submit(worker, p) for p in pending]
            for f in as_completed(futures):
                exc = f.exception()
                if exc:
                    # Cancel remaining tasks on error
                    for other in futures:
                        other.cancel()
                    raise exc
        print()  # newline

    def _sequential_download(self, file_size: int) -> None:
        """Fallback download implementation when Range is unsupported."""
        # Determine resume position
        existing_size = 0
        if self.dest.exists():
            existing_size = os.path.getsize(self.dest)
            # If the existing file is larger than expected, discard it and start over.
            if existing_size > file_size:
                existing_size = 0
                # Truncate file to zero before restarting download
                with open(self.dest, "wb"):
                    pass
        url = self.urls[0]
        headers = {}
        if existing_size > 0:
            headers["Range"] = f"bytes={existing_size}-"
        with self.session.get(url, headers=headers, stream=True, timeout=self.timeout) as resp:
            if resp.status_code not in (200, 206):
                raise DownloadError(f"Sequential download failed: {resp.status_code}")
            with open(self.dest, "ab") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        # Mark all pieces as done and compute sha256s
        pieces = self._load_pieces()
        with open(self.dest, "rb") as f:
            for piece in pieces:
                f.seek(piece.start)
                data = f.read(piece.end - piece.start + 1)
                piece.sha256 = hashlib.sha256(data).hexdigest()
                piece.status = "done"
                piece.last_url = url
                self._save_piece(piece)
