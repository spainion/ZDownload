"""Utility functions for scraping web pages and optionally summarising them.

This module provides a simple web scraping helper that can fetch a web page,
extract key elements such as the title, paragraphs, headings, images, meta
tags, and hyperlinks, and return the information as a structured dictionary.
It optionally integrates with the existing suggestion system to summarise the
page content using an LLM via OpenRouter. The helper respects the
``network_enabled`` configuration flag so that offline runs avoid making
external HTTP requests.

Note: This scraper is intentionally lightweight and does not attempt to
provide the full feature set of the upstream ``Zamida FS Interpreter``. It
avoids dependencies on third‑party parsing libraries by using Python's
built‑in ``html.parser`` module. If you wish to add more sophisticated
scraping features (e.g. CSS selectors, JavaScript execution), consider
installing ``beautifulsoup4`` or ``playwright`` and extending this module.
"""

from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from html.parser import HTMLParser
from typing import Any, Dict, List, Tuple

from .config import Config
from . import suggestions

class _SimpleHTMLParser(HTMLParser):
    """A minimal HTML parser that extracts text, headings, images, meta and links.

    This parser accumulates the contents of ``<title>`` and ``<p>`` tags as
    simple text. It also collects headings (h1–h6), image ``src`` attributes,
    meta tag name–content pairs, and hyperlink ``href`` attributes. The data is
    stored on the instance in lists that can be accessed after parsing.
    """

    def __init__(self) -> None:
        super().__init__()
        self.in_title = False
        self.in_heading: bool = False
        self.current_heading: str = ""
        self.title: str = ""
        self.paragraphs: List[str] = []
        self.headings: List[str] = []
        self.images: List[str] = []
        self.meta: Dict[str, str] = {}
        self.links: List[str] = []
        self._current_data: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, str]]) -> None:
        tag_lower = tag.lower()
        if tag_lower == "title":
            self.in_title = True
            self._current_data = []
        elif tag_lower == "p":
            self._current_data = []
        elif tag_lower in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.in_heading = True
            self._current_data = []
        elif tag_lower == "img":
            # Extract src attribute
            attrs_dict = dict(attrs)
            src = attrs_dict.get("src")
            if src:
                self.images.append(src)
        elif tag_lower == "meta":
            attrs_dict = dict(attrs)
            name = attrs_dict.get("name") or attrs_dict.get("property")
            content = attrs_dict.get("content")
            if name and content:
                self.meta[name] = content
        elif tag_lower == "a":
            attrs_dict = dict(attrs)
            href = attrs_dict.get("href")
            if href:
                self.links.append(href)

    def handle_endtag(self, tag: str) -> None:
        tag_lower = tag.lower()
        if tag_lower == "title" and self.in_title:
            self.title = "".join(self._current_data).strip()
            self.in_title = False
            self._current_data = []
        elif tag_lower == "p":
            text = "".join(self._current_data).strip()
            if text:
                self.paragraphs.append(text)
            self._current_data = []
        elif tag_lower in {"h1", "h2", "h3", "h4", "h5", "h6"} and self.in_heading:
            heading_text = "".join(self._current_data).strip()
            if heading_text:
                self.headings.append(heading_text)
            self.in_heading = False
            self._current_data = []

    def handle_data(self, data: str) -> None:
        # Accumulate data only when capturing title, heading or paragraph
        if self.in_title or self.in_heading or self._current_data is not None:
            self._current_data.append(data)

# -----------------------------------------------------------------------------
# HTTP session with retries and user‑agent
#
# To improve resilience of the scraper we create a singleton requests.Session
# configured with automatic retries and a custom User‑Agent.  This avoids
# repeatedly establishing new TCP connections for each request and provides
# simple retry/backoff behaviour on transient network errors.
_SESSION: requests.Session | None = None

def _get_session() -> requests.Session:
    """Return a shared requests session with retry/backoff and headers.

    The session is lazily initialised the first time it is requested.  It
    mounts an HTTPAdapter that retries idempotent requests on common
    server errors (5xx) and sets a User‑Agent identifying the application.
    """
    global _SESSION
    if _SESSION is None:
        session = requests.Session()
        # Configure retries: 3 attempts with exponential backoff up to ~3 seconds
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=(500, 502, 503, 504),
            allowed_methods=("GET", "HEAD"),
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({
            "User-Agent": "ZDownloadManager/1.0 (+https://github.com/spainion/ZDownload)",
            # Accept language to improve localisation of responses
            "Accept-Language": "en-US,en;q=0.9",
        })
        _SESSION = session
    return _SESSION


def scrape_page(
    url: str,
    *,
    headings: bool = False,
    images: bool = False,
    meta: bool = False,
    summary: bool = False,
    links: bool = False,
    timeout: float = 10.0,
    ) -> Dict[str, Any]:
    """Fetch a single web page and extract selected elements.

    Parameters
    ----------
    url: str
        The page URL to fetch.
    headings: bool, optional
        Whether to include headings (h1–h6) in the returned data.
    images: bool, optional
        Whether to include image sources in the returned data.
    meta: bool, optional
        Whether to include meta tag name–content pairs in the returned data.
    summary: bool, optional
        If ``True`` and network is enabled, generate a natural language
        summary of the page content via the suggestion system.
    links: bool, optional
        Whether to include hyperlink targets in the returned data.
    timeout: float, optional
        Timeout in seconds for the HTTP request (default 10 seconds).

    Returns
    -------
    Dict[str, Any]
        A dictionary containing extracted fields. Keys always present are
        ``title`` and ``text`` (concatenated paragraphs). Optional keys
        include ``headings``, ``images``, ``meta``, ``links``, and ``summary``.
    """
    cfg = Config()
    # If network is disabled via config, don't attempt to fetch
    if not cfg.data.get("network_enabled", True):
        return {"error": "Network access is disabled in configuration"}
    # Use the shared session for connection pooling and retries
    session = _get_session()
    try:
        resp = session.get(url, timeout=timeout)
        resp.raise_for_status()
    except Exception as e:
        return {"error": f"Failed to fetch URL: {e}"}
    content_type = resp.headers.get("Content-Type", "")
    # Only parse HTML content
    if not content_type.lower().startswith("text/html") and "json" not in content_type.lower():
        return {"error": f"Unsupported content type: {content_type}"}
    html = resp.text
    parser = _SimpleHTMLParser()
    try:
        parser.feed(html)
        parser.close()
    except Exception:
        # Ignore malformed HTML errors
        pass
    data: Dict[str, Any] = {}
    data["title"] = parser.title or url
    # Concatenate paragraphs into a single text block
    data["text"] = "\n\n".join(parser.paragraphs)
    if headings:
        data["headings"] = parser.headings
    if images:
        data["images"] = parser.images
    if meta:
        data["meta"] = parser.meta
    if links:
        data["links"] = parser.links
    if summary:
        # Use the suggestions API to summarise the page content if network is enabled
        question = f"Summarise the following web page.\n\nTitle: {data['title']}\nContent:\n{data['text'][:1500]}"
        # Limit content length to avoid hitting context limits
        if cfg.data.get("network_enabled", True):
            try:
                answer = suggestions.get_suggestion(cfg, question)
                data["summary"] = answer
            except Exception as exc:
                data["summary"] = f"Failed to generate summary: {exc}"
        else:
            data["summary"] = "Summary unavailable: network disabled"
    return data


def scrape_links(url: str, *, timeout: float = 10.0) -> List[str]:
    """Fetch a web page and return all hyperlinks found on it.

    Parameters
    ----------
    url: str
        The page URL to fetch.
    timeout: float, optional
        Timeout in seconds for the HTTP request (default 10 seconds).

    Returns
    -------
    List[str]
        A list of href values from anchor tags on the page. Duplicates are
        removed while preserving order.
    """
    cfg = Config()
    if not cfg.data.get("network_enabled", True):
        return []
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
    except Exception:
        return []
    parser = _SimpleHTMLParser()
    try:
        parser.feed(resp.text)
        parser.close()
    except Exception:
        pass
    # Deduplicate links preserving order
    seen = set()
    deduped: List[str] = []
    for link in parser.links:
        if link not in seen:
            deduped.append(link)
            seen.add(link)
    return deduped


def scrape_site(
    url: str,
    *,
    depth: int = 1,
    headings: bool = False,
    images: bool = False,
    meta: bool = False,
    summary: bool = False,
    links: bool = False,
    timeout: float = 10.0,
    parallel: bool = False,
    max_workers: int = 4,
    ) -> Dict[str, Any]:
    """Recursively scrape a website up to a given depth.

    This helper fetches the initial page and, if ``depth`` is greater than
    zero, follows hyperlinks up to ``depth`` levels deep. It aggregates data
    about all visited pages in a dictionary keyed by URL. Recursion stops when
    the depth counter reaches zero.

    Parameters
    ----------
    url: str
        The root page to start scraping from.
    depth: int, optional
        How many levels of links to traverse (default 1). A depth of 0
        returns only the root page. Negative values behave like 0.
    headings, images, meta, summary, links: bool, optional
        Same meaning as in :func:`scrape_page`.
    timeout: float, optional
        Timeout for each HTTP request.

    Returns
    -------
    Dict[str, Any]
        A mapping from visited URL to the extracted data for that page. If
        fetching any page fails, it will include an ``error`` field for that
        entry.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    # Normalise depth
    depth = max(depth, 0)
    results: Dict[str, Any] = {}
    visited: set[str] = set()
    # Seed with the initial URL and level
    to_visit: List[Tuple[str, int]] = [(url, 0)]

    while to_visit:
        # Optionally process in parallel
        if parallel:
            futures = {}
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                for current_url, lvl in to_visit:
                    if current_url in visited:
                        continue
                    visited.add(current_url)
                    futures[executor.submit(
                        scrape_page,
                        current_url,
                        headings=headings,
                        images=images,
                        meta=meta,
                        summary=summary,
                        links=links,
                        timeout=timeout,
                    )] = (current_url, lvl)
                # Reset to_visit for next level accumulation
                to_visit = []
                for future in as_completed(futures):
                    current_url, lvl = futures[future]
                    try:
                        page_data = future.result()
                    except Exception as exc:
                        page_data = {"error": f"Unhandled exception: {exc}"}
                    results[current_url] = page_data
                    if lvl < depth and isinstance(page_data.get("links"), list):
                        for link in page_data["links"]:
                            if link not in visited:
                                to_visit.append((link, lvl + 1))
        else:
            current_url, lvl = to_visit.pop()
            if current_url in visited:
                continue
            visited.add(current_url)
            page_data = scrape_page(
                current_url,
                headings=headings,
                images=images,
                meta=meta,
                summary=summary,
                links=links,
                timeout=timeout,
            )
            results[current_url] = page_data
            if lvl < depth and isinstance(page_data.get("links"), list):
                for link in page_data["links"]:
                    if link not in visited:
                        to_visit.append((link, lvl + 1))
    return results
