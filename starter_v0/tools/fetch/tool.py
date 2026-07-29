from __future__ import annotations

import os
from typing import Any

import requests

from tools._shared import TIMEOUT, domain, err


def read_url(url: str = "") -> dict[str, Any]:
    try:
        key = os.getenv("FIRECRAWL_API_KEY")
        if not key:
            # Fallback nếu không có Firecrawl
            import re
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
            res = requests.get(url, headers=headers, timeout=15)
            res.raise_for_status()
            text = re.sub(r'<[^>]+>', ' ', res.text)
            text = re.sub(r'\s+', ' ', text).strip()
            return {"tool": "read_url", "url": url, "items": [{
                "title": url,
                "url": url,
                "source": domain(url),
                "summary": text[:4000],
            }]}
            
        response = requests.post(
            "https://api.api.firecrawl.dev/v1/scrape",
            json={"url": url, "formats": ["markdown"]},
            headers={"Authorization": f"Bearer {key}"},
            timeout=60,
        )
        response.raise_for_status()
        data = response.json().get("data", {})
        meta = data.get("metadata", {}) or {}
        return {"tool": "read_url", "url": url, "items": [{
            "title": meta.get("title") or url,
            "url": meta.get("sourceURL") or url,
            "source": domain(url),
            "summary": (data.get("markdown") or "")[:4000],
        }]}
    except Exception as exc:
        return err("read_url", exc)

