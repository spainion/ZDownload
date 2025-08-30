"""Protocol handler for custom zdm:// URLs.

This small utility enables other applications to launch ZDownloadManager via a
custom URI scheme. Example:

```
zdm-proto "zdm://download?url=https%3A%2F%2Fexample.com%2Ffile.iso&dest=%2Ftmp%2Ffile.iso"
```

It decodes the parameters and forwards them to the CLI interface.
"""
from __future__ import annotations

import argparse
import urllib.parse
from typing import Optional

from ..cli import main as cli_main


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Handle zdm:// protocol URI")
    parser.add_argument("uri", help="zdm protocol URI")
    args = parser.parse_args(argv)
    uri = args.uri
    if not uri.startswith("zdm://"):
        raise SystemExit("Invalid URI scheme; must start with zdm://")
    # Remove scheme
    path = uri[len("zdm://"):]
    if "?" not in path:
        raise SystemExit("Invalid zdm URI; missing parameters")
    action, query = path.split("?", 1)
    params = urllib.parse.parse_qs(query)
    url = params.get("url", [None])[0]
    dest = params.get("dest", [None])[0]
    mirrors = params.get("mirrors", [""])[0]
    piece = params.get("piece", [None])[0]
    conc = params.get("conc", [None])[0]
    cli_args = [url]
    if dest:
        cli_args.extend(["-o", dest])
    if mirrors:
        cli_args.extend(["--mirrors", mirrors])
    if piece:
        cli_args.extend(["--piece", piece])
    if conc:
        cli_args.extend(["--conc", conc])
    cli_main(cli_args)


if __name__ == "__main__":
    main()
