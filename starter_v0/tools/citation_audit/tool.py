from __future__ import annotations

import re
from typing import Any


URL_PATTERN = re.compile(r"https?://[^\s)\]>]+")


def audit_citations(draft: str = "", allowed_urls: list[str] | None = None) -> dict[str, Any]:
    """Check whether URLs cited in a draft belong to the supplied source set."""
    allowed = sorted({url.rstrip(".,;:") for url in (allowed_urls or []) if url})
    cited = sorted({url.rstrip(".,;:") for url in URL_PATTERN.findall(draft)})
    allowed_set = set(allowed)
    cited_set = set(cited)
    return {
        "tool": "audit_citations",
        "citation_count": len(cited),
        "cited_urls": cited,
        "missing_from_sources": sorted(cited_set - allowed_set),
        "unused_sources": sorted(allowed_set - cited_set),
        "all_citations_known": cited_set.issubset(allowed_set),
    }
