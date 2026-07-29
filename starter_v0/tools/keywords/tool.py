from __future__ import annotations

from collections import Counter
from typing import Any

from tools._shared import terms


def extract_keywords(text: str = "", max_keywords: int = 8) -> dict[str, Any]:
    """Extract frequent, non-stopword terms from already available text."""
    limit = max(1, min(int(max_keywords or 8), 20))
    counts = Counter(terms(text))
    keywords = [
        {"term": term, "count": count}
        for term, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]
    ]
    return {
        "tool": "extract_keywords",
        "keyword_count": len(keywords),
        "keywords": keywords,
    }
