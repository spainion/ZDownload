import json
import os
import subprocess
import sys
import tempfile
import unittest

from zdownloadmanager import __version__


class CLITests(unittest.TestCase):
    def test_version_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "HOME": tmp}
            out = subprocess.check_output(
                [sys.executable, "-m", "zdownloadmanager.cli", "--version"], env=env, text=True
            ).strip()
            self.assertEqual(out, __version__)

    def test_show_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "HOME": tmp}
            proc = subprocess.run(
                [sys.executable, "-m", "zdownloadmanager.cli", "--show-config"],
                env=env,
                stdout=subprocess.PIPE,
                text=True,
                check=True,
            )
            data = json.loads(proc.stdout)
            self.assertIn("piece_size", data)

    def test_show_snapshots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "HOME": tmp}
            out_ctx = subprocess.check_output(
                [sys.executable, "-m", "zdownloadmanager.cli", "--show-context-snapshot"],
                env=env,
                text=True,
            )
            self.assertIn("# File:", out_ctx)
            out_code = subprocess.check_output(
                [sys.executable, "-m", "zdownloadmanager.cli", "--show-code-snapshot"],
                env=env,
                text=True,
            )
            self.assertIn("# Code Snapshot", out_code)

    def test_verify_snapshots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "HOME": tmp}
            proc = subprocess.run(
                [sys.executable, "-m", "zdownloadmanager.cli", "--verify-snapshots"],
                env=env,
                stdout=subprocess.PIPE,
                text=True,
                check=True,
            )
            self.assertIn("Snapshots up to date", proc.stdout)

    @unittest.skipUnless(os.getenv("OPENROUTER_API_KEY"), "OPENROUTER_API_KEY not set")
    def test_list_models(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "HOME": tmp}
            out = subprocess.check_output(
                [sys.executable, "-m", "zdownloadmanager.cli", "--list-models"],
                env=env,
                text=True,
            )
            self.assertIn("data", out)

    def test_dependency_queries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "HOME": tmp}
            deps = subprocess.check_output(
                [
                    sys.executable,
                    "-m",
                    "zdownloadmanager.cli",
                    "--show-dependencies",
                    "ZDownloadManager/zdownloadmanager/cli.py",
                ],
                env=env,
                text=True,
            )
            self.assertIn(
                "ZDownloadManager/zdownloadmanager/core/config.py",
                deps,
            )
            dependents = subprocess.check_output(
                [
                    sys.executable,
                    "-m",
                    "zdownloadmanager.cli",
                    "--show-dependents",
                    "ZDownloadManager/zdownloadmanager/core/config.py",
                ],
                env=env,
                text=True,
            )
            self.assertIn(
                "ZDownloadManager/zdownloadmanager/cli.py",
                dependents,
            )


if __name__ == "__main__":
    unittest.main()
