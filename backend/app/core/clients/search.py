"""Web search (SearXNG) and page text extraction."""
from dataclasses import dataclass

import httpx
import trafilatura

from app.core.config import settings

SKIP_DOMAINS = ("youtube.com", "tiktok.com", "instagram.com", "facebook.com", "pinterest.")


@dataclass
class Result:
    title: str
    url: str
    snippet: str


def search(query: str, limit: int = 10) -> list[Result]:
    resp = httpx.get(f"{settings.search_url}/search", params={"q": query, "format": "json"}, timeout=30)
    resp.raise_for_status()
    results = [
        Result(r.get("title", ""), r["url"], r.get("content", ""))
        for r in resp.json()["results"]
        if not any(d in r["url"] for d in SKIP_DOMAINS)
    ]
    return results[:limit]


def page_text(url: str, max_chars: int = 4000) -> str:
    """Main article text of a page, or '' if it cannot be read."""
    try:
        html = httpx.get(url, timeout=15, follow_redirects=True,
                         headers={"User-Agent": "Mozilla/5.0"}).text
    except httpx.HTTPError:
        return ""
    return (trafilatura.extract(html) or "")[:max_chars]
