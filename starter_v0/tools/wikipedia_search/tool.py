from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, domain, err

# MediaWiki API requires a user-agent header to avoid 403 Forbidden errors
HEADERS = {
    "User-Agent": "ResearchAssistantApp/1.0 (contact: admin@example.com)"
}


def search_wikipedia(query: str = "", lang: str = "en", limit: int = 3, summary: bool = True) -> dict[str, Any]:
    """Search Wikipedia and return a list of pages.

    Uses the MediaWiki search API (no API key required). Returns a dict with
    keys: tool, query, lang, limit, items.
    Each item is: {title, url, source, summary}.
    """
    try:
        if not query:
            raise ValueError("Missing query")
        # Build search API endpoint
        endpoint = f"https://{lang}.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": int(limit or 3),
            "format": "json",
        }
        # Fixed: Added headers=HEADERS to avoid 403 Forbidden
        resp = requests.get(endpoint, params=params, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        search_hits = data.get("query", {}).get("search", [])
        items = []
        for hit in search_hits[: int(limit or 3)]:
            title = hit.get("title")
            page_url = f"https://{lang}.wikipedia.org/wiki/{title.replace(' ', '_')}" if title else ""
            item_summary = ""
            if summary:
                # Try to fetch extract via the API
                extract_params = {
                    "action": "query",
                    "prop": "extracts",
                    "exintro": "1",
                    "titles": title,
                    "format": "json",
                    "explaintext": "1",
                }
                try:
                    # Fixed: Added headers=HEADERS here as well
                    ex_resp = requests.get(endpoint, params=extract_params, headers=HEADERS, timeout=TIMEOUT)
                    ex_resp.raise_for_status()
                    ex_data = ex_resp.json()
                    pages = ex_data.get("query", {}).get("pages", {})
                    # pages is a dict keyed by pageid
                    for p in pages.values():
                        item_summary = p.get("extract", "") or ""
                        break
                except Exception:
                    item_summary = ""
            items.append({
                "title": title,
                "url": page_url,
                "source": domain(page_url),
                "summary": item_summary,
            })
        return {"tool": "wikipedia_search", "query": query, "lang": lang, "limit": int(limit or 3), "items": items}
    except Exception as exc:
        return err("wikipedia_search", exc)