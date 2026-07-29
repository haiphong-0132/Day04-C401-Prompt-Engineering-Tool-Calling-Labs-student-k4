from __future__ import annotations

import os
from typing import Any

import requests

from tools._shared import TIMEOUT, err


def get_user_tweets(screenname: str = "", limit: int = 5) -> dict[str, Any]:
    try:
        key = os.getenv("SERP_API_KEY")
        endpoint = os.getenv("SERP_ENDPOINT", "https://serpapi.com/search")
        if not key:
            raise RuntimeError("Missing SERP_API_KEY env var")
            
        # The endpoint in env might contain ?engine=google. We'll extract base url.
        base_url = endpoint.split("?")[0]
        params = {
            "engine": "google",
            "q": f"site:x.com/{screenname} OR site:twitter.com/{screenname}",
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
                "source": f"@{screenname}",
            })
            
        return {"tool": "get_user_tweets", "screenname": screenname, "items": items}
    except Exception as exc:
        return err("get_user_tweets", exc)

