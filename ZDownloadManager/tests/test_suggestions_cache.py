import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from zdownloadmanager.core.config import Config
from zdownloadmanager.core.suggestions import (
    get_suggestion,
    clear_cache,
    stream_suggestion,
    _cache_file,
)


@unittest.skipUnless(os.getenv("OPENROUTER_API_KEY"), "OPENROUTER_API_KEY not set")
class SuggestionCacheTest(unittest.TestCase):
    def test_cache_reuse_without_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg_path = Path(tmp) / "config.json"
            cfg = Config(cfg_path)
            cfg.update(suggestions_enabled=True, openrouter_api_key=os.environ["OPENROUTER_API_KEY"])
            question = "What is 2+2?"
            answer1 = get_suggestion(cfg, question)
            self.assertIsNotNone(answer1)
            cache_path = _cache_file(cfg)
            self.assertTrue(cache_path.exists())
            cfg.update(openrouter_api_key="")
            answer2 = get_suggestion(cfg, question)
            self.assertEqual(answer1, answer2)
            cleared = clear_cache(cfg)
            self.assertTrue(cleared)
            self.assertFalse(cache_path.exists())

    def test_cli_show_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "HOME": tmp}
            cfg_dir = Path(tmp) / ".config" / "zdownloadmanager"
            cfg_dir.mkdir(parents=True, exist_ok=True)
            cfg = Config(cfg_dir / "config.json")
            cfg.update(
                suggestions_enabled=True,
                openrouter_api_key=os.environ["OPENROUTER_API_KEY"],
            )
            question = "What is 2+2?"
            subprocess.check_output(
                [
                    sys.executable,
                    "-m",
                    "zdownloadmanager.cli",
                    "--suggest",
                    question,
                ],
                env=env,
                text=True,
            )
            out = subprocess.check_output(
                [sys.executable, "-m", "zdownloadmanager.cli", "--show-suggestions-cache"],
                env=env,
                text=True,
            )
            self.assertIn(question, out)

    def test_custom_model(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg_path = Path(tmp) / "config.json"
            cfg = Config(cfg_path)
            cfg.update(
                suggestions_enabled=True,
                openrouter_api_key=os.environ["OPENROUTER_API_KEY"],
                openrouter_model="openai/gpt-4o-mini",
            )
            question = "Say hello"
            answer = get_suggestion(cfg, question)
            self.assertIsNotNone(answer)

    def test_cli_custom_model(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "HOME": tmp}
            cfg_dir = Path(tmp) / ".config" / "zdownloadmanager"
            cfg_dir.mkdir(parents=True, exist_ok=True)
            cfg = Config(cfg_dir / "config.json")
            cfg.update(
                suggestions_enabled=True,
                openrouter_api_key=os.environ["OPENROUTER_API_KEY"],
            )
            question = "Hi"
            subprocess.check_output(
                [
                    sys.executable,
                    "-m",
                    "zdownloadmanager.cli",
                    "--suggest",
                    question,
                    "--suggest-model",
                    "openai/gpt-4o-mini",
                ],
                env=env,
                text=True,
            )
            cfg_reloaded = Config(cfg_dir / "config.json")
            self.assertEqual(cfg_reloaded.openrouter_model, "openai/gpt-4o-mini")

    def test_cli_custom_params(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "HOME": tmp}
            cfg_dir = Path(tmp) / ".config" / "zdownloadmanager"
            cfg_dir.mkdir(parents=True, exist_ok=True)
            cfg = Config(cfg_dir / "config.json")
            cfg.update(
                suggestions_enabled=True,
                openrouter_api_key=os.environ["OPENROUTER_API_KEY"],
            )
            question = "Hello"
            subprocess.check_output(
                [
                    sys.executable,
                    "-m",
                    "zdownloadmanager.cli",
                    "--suggest",
                    question,
                    "--suggest-temperature",
                    "0.5",
                    "--suggest-max-tokens",
                    "50",
                    "--suggest-top-p",
                    "0.9",
                ],
                env=env,
                text=True,
            )
            cfg_reloaded = Config(cfg_dir / "config.json")
            self.assertAlmostEqual(cfg_reloaded.openrouter_temperature, 0.5)
            self.assertEqual(cfg_reloaded.openrouter_max_tokens, 50)
            self.assertAlmostEqual(cfg_reloaded.openrouter_top_p, 0.9)

    def test_streaming(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg_path = Path(tmp) / "config.json"
            cfg = Config(cfg_path)
            cfg.update(
                suggestions_enabled=True,
                openrouter_api_key=os.environ["OPENROUTER_API_KEY"],
            )
            question = "Name a color"
            parts = list(stream_suggestion(cfg, question))
            answer = "".join(parts)
            self.assertTrue(answer)

    def test_cli_stream(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "HOME": tmp}
            cfg_dir = Path(tmp) / ".config" / "zdownloadmanager"
            cfg_dir.mkdir(parents=True, exist_ok=True)
            cfg = Config(cfg_dir / "config.json")
            cfg.update(
                suggestions_enabled=True,
                openrouter_api_key=os.environ["OPENROUTER_API_KEY"],
            )
            question = "Hello"
            out = subprocess.check_output(
                [
                    sys.executable,
                    "-m",
                    "zdownloadmanager.cli",
                    "--suggest-stream",
                    question,
                ],
                env=env,
                text=True,
            )
            self.assertTrue(out.strip())


if __name__ == "__main__":
    unittest.main()
