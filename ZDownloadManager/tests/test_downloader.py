import os
import tempfile
import unittest
from pathlib import Path

from zdownloadmanager.core.downloader import SegmentedDownloader


class DownloaderTests(unittest.TestCase):
    def test_download_example(self) -> None:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            dest_path = Path(tmp.name)
        try:
            url = "https://raw.githubusercontent.com/github/gitignore/main/Python.gitignore"
            dl = SegmentedDownloader([url], dest_path, piece_size=1024, concurrency=1)
            dl.session.headers["Accept-Encoding"] = "identity"
            dl.download()
            self.assertTrue(dest_path.exists())
            self.assertGreater(dest_path.stat().st_size, 0)
        finally:
            if dest_path.exists():
                os.remove(dest_path)


if __name__ == "__main__":
    unittest.main()
