"""Deduplication of candidate entries against the recall store."""

from __future__ import annotations

from recall.models import Entry
from recall.store import Store


def deduplicate(
    candidates: list[Entry],
    store: Store,
    *,
    similarity_threshold: float = 0.7,
) -> list[Entry]:
    """Filter out candidates that are too similar to existing recall entries.

    For each candidate:
    1. FTS5 search with first 80 chars to find potential matches
    2. Token-overlap scoring against top results
    3. Skip if overlap > threshold
    """
    unique: list[Entry] = []

    for candidate in candidates:
        query = candidate.content[:80].strip()
        if not query:
            continue

        try:
            results = store.search(query, limit=3)
        except Exception:
            # If search fails (empty query, FTS syntax error), keep the candidate
            unique.append(candidate)
            continue

        is_duplicate = False
        for result in results:
            overlap = _token_overlap(candidate.content, result.entry.content)
            if overlap >= similarity_threshold:
                is_duplicate = True
                break

        if not is_duplicate:
            unique.append(candidate)

    return unique


def _token_overlap(a: str, b: str) -> float:
    """Jaccard similarity on word tokens, lowercased."""
    tokens_a = set(a.lower().split())
    tokens_b = set(b.lower().split())

    if not tokens_a or not tokens_b:
        return 0.0

    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b

    return len(intersection) / len(union)
