"""Hacker News adapter via the Algolia HN Search API (no auth required)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx

from digest.expansion import ExpandedQuery
from digest.models import Item

ALGOLIA_URL = "https://hn.algolia.com/api/v1/search"


class HackerNewsAdapter:
    name = "hn"

    def fetch(self, query: ExpandedQuery, days: int, limit: int = 50) -> list[Item]:
        """Fetch stories matching any HN expansion term.

        Uses `effective_hn_terms` (HN-specific terms if present, else generic).
        Algolia's HN search is AND-biased within a query string, so we run one
        search per term and dedupe by objectID. Per-term limits keep the total
        fetch size bounded regardless of expansion breadth.
        """
        since = datetime.now(timezone.utc) - timedelta(days=days)
        terms = query.effective_hn_terms
        per_term_limit = max(limit // max(len(terms), 1), 10)

        seen: dict[str, Item] = {}
        for term in terms:
            hits = self._search_term(term, since, per_term_limit)
            for hit in hits:
                if hit["objectID"] not in seen:
                    seen[hit["objectID"]] = self._build_item(hit)

        return list(seen.values())[:limit]

    def _search_term(
        self, term: str, since: datetime, limit: int
    ) -> list[dict]:
        params = {
            "query": term,
            "tags": "story",
            "numericFilters": f"created_at_i>{int(since.timestamp())}",
            "hitsPerPage": limit,
        }
        response = httpx.get(ALGOLIA_URL, params=params, timeout=30.0)
        response.raise_for_status()
        return response.json().get("hits", [])

    def _build_item(self, hit: dict) -> Item:
        url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit['objectID']}"
        points = hit.get("points") or 0
        num_comments = hit.get("num_comments") or 0
        return Item(
            source=self.name,
            title=hit.get("title") or "",
            url=url,
            author=hit.get("author"),
            timestamp=datetime.fromtimestamp(hit["created_at_i"], tz=timezone.utc),
            engagement=points + num_comments,
            raw={
                "object_id": hit["objectID"],
                "points": points,
                "num_comments": num_comments,
            },
        )
