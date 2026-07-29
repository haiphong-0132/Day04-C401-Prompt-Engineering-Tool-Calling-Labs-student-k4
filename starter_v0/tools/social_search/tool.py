from __future__ import annotations

import os
from typing import Any

import requests

from tools._shared import TIMEOUT, err


def search_tweets(query: str = "", search_type: str = "Latest", limit: int = 5) -> dict[str, Any]:
    try:
        key = os.getenv("SERP_API_KEY")
        endpoint = os.getenv("SERP_ENDPOINT", "https://serpapi.com/search")
        if not key:
            raise RuntimeError("Missing SERP_API_KEY env var")
            
        base_url = endpoint.split("?")[0]
        params = {
            "engine": "google",
            "q": f"site:x.com OR site:twitter.com {query}",
            "api_key": key,
            "num": limit or 5
        }
        
        response = requests.get(base_url, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        raw_items = data.get("organic_results", [])
        items = []
        for r in raw_items[: int(limit or 5)]:
            items.append({
                "title": r.get("title", "")[:120],
                "summary": r.get("snippet", ""),
                "url": r.get("link", ""),
                "source": "x.com",
            })
            
        return {"tool": "search_tweets", "query": query, "search_type": search_type, "items": items}
    except Exception as exc:
        return err("search_tweets", exc)

