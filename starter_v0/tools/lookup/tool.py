from __future__ import annotations

import os
from typing import Any

import requests

from tools._shared import TIMEOUT, domain, err


def web_search(query: str = "", topic: str = "general", timeframe: str | None = "week", max_results: int = 5) -> dict[str, Any]:
    try:
        key = os.getenv("SERP_API_KEY")
        if not key:
            raise RuntimeError("Missing SERP_API_KEY env var. Vui lòng nhập key trong file .env")
            
        endpoint = os.getenv("SERP_ENDPOINT", "https://serpapi.com/search")
        response = requests.get(
            endpoint,
            params={"engine": "google", "q": query, "api_key": key},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        
        items = [{
            "title": item.get("title"),
            "url": item.get("link"),
            "source": domain(item.get("link", "")),
            "summary": item.get("snippet"),
        } for item in data.get("organic_results", [])[:max_results]]
        
        return {"tool": "web_search", "query": query, "topic": topic, "timeframe": timeframe, "items": items}
    except Exception as exc:
        return err("web_search", exc)

