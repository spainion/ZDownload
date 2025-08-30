import json
import subprocess
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "context_snapshot.py"


class ContextSnapshotTest(unittest.TestCase):
    def test_snapshot_created(self) -> None:
        subprocess.check_call([sys.executable, str(SCRIPT)], cwd=ROOT)
        md_path = ROOT / "context_snapshot.md"
        json_path = ROOT / "context_snapshot.json"
        self.assertTrue(md_path.exists())
        self.assertTrue(json_path.exists())
        content = md_path.read_text(encoding="utf-8")
        self.assertIn("ZDownload", content)
        data = json.loads(json_path.read_text(encoding="utf-8"))
        self.assertIn("status", data)
        deps = data.get("dependencies", {})
        cli_file = "ZDownloadManager/zdownloadmanager/cli.py"
        self.assertIn(cli_file, deps)
        self.assertTrue(any(d.endswith("core/config.py") for d in deps[cli_file]))


if __name__ == "__main__":
    unittest.main()
