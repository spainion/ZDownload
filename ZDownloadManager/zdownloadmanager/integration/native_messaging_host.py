"""Native messaging host for Chrome integration.

This script implements the communication protocol required by Chrome's
Native Messaging API. The browser extension sends a JSON object containing
download parameters, and the host forwards them to the CLI downloader. The
resulting response is returned as JSON. All messages are framed with a
32‑bit little‑endian length prefix.
"""
from __future__ import annotations

import json
import struct
import sys
from typing import Any, Dict, Optional

from ..cli import main as cli_main


def read_message() -> Optional[Dict[str, Any]]:
    """Read a message from stdin. Returns None on EOF."""
    raw_length = sys.stdin.buffer.read(4)
    if len(raw_length) == 0:
        return None
    message_length = struct.unpack("<I", raw_length)[0]
    message = sys.stdin.buffer.read(message_length)
    try:
        return json.loads(message.decode("utf-8"))
    except json.JSONDecodeError:
        return None


def write_message(msg: Dict[str, Any]) -> None:
    data = json.dumps(msg).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("<I", len(data)))
    sys.stdout.buffer.write(data)
    sys.stdout.buffer.flush()


def main() -> None:
    while True:
        msg = read_message()
        if msg is None:
            break
        # Expect keys: url, dest, mirrors, piece, conc
        url = msg.get("url")
        if not url:
            write_message({"error": "Missing url"})
            continue
        dest = msg.get("dest")
        mirrors = msg.get("mirrors", "")
        piece = msg.get("piece")
        conc = msg.get("conc")
        cli_args = [url]
        if dest:
            cli_args.extend(["-o", dest])
        if mirrors:
            cli_args.extend(["--mirrors", mirrors])
        if piece:
            cli_args.extend(["--piece", str(piece)])
        if conc:
            cli_args.extend(["--conc", str(conc)])
        try:
            cli_main(cli_args)
            write_message({"status": "ok"})
        except Exception as e:
            write_message({"error": str(e)})


if __name__ == "__main__":
    main()
