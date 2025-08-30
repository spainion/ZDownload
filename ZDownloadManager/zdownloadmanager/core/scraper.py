"""Simple web scraper utilities."""
from __future__ import annotations

from typing import List, Optional

import requests
from bs4 import BeautifulSoup


def scrape_links(url: str, extensions: Optional[List[str]] = None) -> List[str]:
    """Return links found on *url* optionally filtered by file extensions.

    Args:
        url: Web page to fetch.
        extensions: Optional list of suffixes (e.g. [".zip"]). When provided,
            only links ending with one of these suffixes are returned.

    Returns:
        A list of link URLs discovered on the page.
    """
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    links: List[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if extensions:
            if any(href.lower().endswith(ext.lower()) for ext in extensions):
                links.append(href)
        else:
            links.append(href)
    return links
