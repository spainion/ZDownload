import json
import subprocess
import sys
from pathlib import Path


def test_code_scanner_generates_summary(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "scripts" / "code_scan.py"
    out_json = tmp_path / "summary.json"
    subprocess.run([sys.executable, str(script), "--json", str(out_json)], check=True, cwd=repo_root)
    data = json.loads(out_json.read_text())
    key = "ZDownloadManager/zdownloadmanager/cli.py"
    assert key in data
    assert any(sig.startswith("main(") for sig in data[key]["functions"])
