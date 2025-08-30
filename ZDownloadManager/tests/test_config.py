import tempfile
from pathlib import Path
import unittest

from zdownloadmanager.core.config import Config
from zdownloadmanager import __version__


class ConfigTests(unittest.TestCase):
    def test_update_and_reload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg_path = Path(tmpdir) / "config.json"
            cfg = Config(cfg_path)
            cfg.update(
                piece_size=1234,
                concurrency=2,
                suggestions_enabled=True,
                openrouter_api_key="abc",
                openrouter_temperature=0.5,
                openrouter_max_tokens=50,
                openrouter_top_p=0.9,
            )
            cfg2 = Config(cfg_path)
            self.assertEqual(cfg2.piece_size, 1234)
            self.assertEqual(cfg2.concurrency, 2)
            self.assertTrue(cfg2.suggestions_enabled)
            self.assertEqual(cfg2.openrouter_api_key, "abc")
            self.assertAlmostEqual(cfg2.openrouter_temperature, 0.5)
            self.assertEqual(cfg2.openrouter_max_tokens, 50)
            self.assertAlmostEqual(cfg2.openrouter_top_p, 0.9)
            self.assertEqual(cfg2.last_version, __version__)


if __name__ == "__main__":
    unittest.main()
