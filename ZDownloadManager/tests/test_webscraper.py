import unittest

from zdownloadmanager.core.webscraper import scrape_links


class WebScraperTests(unittest.TestCase):
    def test_example_com(self) -> None:
        links = scrape_links("https://example.com")
        self.assertGreaterEqual(len(links), 1)


if __name__ == "__main__":
    unittest.main()
