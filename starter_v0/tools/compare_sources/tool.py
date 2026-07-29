from __future__ import annotations

from typing import Any

from tools._shared import terms


def _item_text(item: dict[str, Any]) -> str:
    return " ".join(str(item.get(field, "")) for field in ("title", "summary", "source"))


def compare_sources(items: list[dict[str, Any]] | None = None, focus: str = "") -> dict[str, Any]:
    """Compare terms shared and unique across already-collected source items."""
    items = items or []
    term_sets = [terms(_item_text(item)) for item in items]
    all_terms = set().union(*term_sets) if term_sets else set()
    shared = set.intersection(*term_sets) if term_sets else set()
    focus_terms = terms(focus)
    if focus_terms:
        all_terms &= focus_terms
        shared &= focus_terms

    source_summaries: list[dict[str, Any]] = []
    for item, item_terms in zip(items, term_sets, strict=False):
        source_summaries.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "unique_terms": sorted(item_terms - shared)[:12],
        })
    return {
        "tool": "compare_sources",
        "source_count": len(items),
        "focus": focus,
        "shared_terms": sorted(shared)[:20],
        "all_terms": sorted(all_terms)[:30],
        "sources": source_summaries,
    }
