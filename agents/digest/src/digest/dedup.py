"""Cross-platform deduplication.

Items are considered duplicates if they share a normalized URL or have
highly similar titles. When duplicates are found, we keep the highest-scoring
one and merge engagement counts.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher

from digest.models import Item
from digest.ranking import score

URL_CLEAN_RE = re.compile(r"^https?://(www\.)?")
TITLE_CLEAN_RE = re.compile(r"[^a-z0-9 ]+")


def _normalize_url(url: str) -> str:
    return URL_CLEAN_RE.sub("", url.rstrip("/").lower())


def _normalize_title(title: str) -> str:
    return TITLE_CLEAN_RE.sub(" ", title.lower()).strip()


def _titles_similar(a: str, b: str, threshold: float = 0.85) -> bool:
    return SequenceMatcher(None, _normalize_title(a), _normalize_title(b)).ratio() >= threshold


def dedupe(items: list[Item]) -> list[Item]:
    """Merge duplicate items across platforms, keeping the best-scoring one."""
    by_url: dict[str, Item] = {}
    for item in items:
        key = _normalize_url(item.url)
        existing = by_url.get(key)
        if existing is None or score(item) > score(existing):
            by_url[key] = item
        else:
            existing.engagement += item.engagement

    # Second pass: merge by title similarity across different URLs.
    merged: list[Item] = []
    for item in by_url.values():
        match = next((m for m in merged if _titles_similar(m.title, item.title)), None)
        if match is None:
            merged.append(item)
        elif score(item) > score(match):
            match.engagement += item.engagement
            merged[merged.index(match)] = item
        else:
            match.engagement += item.engagement
    return merged
