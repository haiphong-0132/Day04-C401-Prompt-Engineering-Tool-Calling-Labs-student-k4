from __future__ import annotations
import urllib.request
import urllib.parse
import json

def get_wikipedia_summary(title: str) -> dict:
    """Fetch the Wikipedia summary for a given title."""
    if not title:
        return {"error": "Missing title"}
    
    encoded_title = urllib.parse.quote(title)
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"
    
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "ResearchAgent/1.0"}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            extract = data.get("extract", "")
            return {"title": data.get("title"), "summary": extract}
    except Exception as e:
        return {"error": f"Failed to fetch Wikipedia summary: {str(e)}"}
