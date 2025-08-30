import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "openrouter_models.py"


@unittest.skipUnless(os.getenv("OPENROUTER_API_KEY"), "OPENROUTER_API_KEY not set")
class OpenRouterModelsTest(unittest.TestCase):
    def test_models_fetch(self) -> None:
        out = subprocess.check_output([sys.executable, str(SCRIPT)], cwd=ROOT, text=True)
        self.assertIn("data", out)


if __name__ == "__main__":
    unittest.main()
