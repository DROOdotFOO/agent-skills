"""ethresear.ch adapter via the Discourse search API (no auth required)."""

from __future__ import annotations

from datetime import datetime, timezone

import httpx

from digest.expansion import ExpandedQuery
from digest.models import Item

SEARCH_URL = "https://ethresear.ch/search.json"
BASE_URL = "https://ethresear.ch"


class EthResearchAdapter:
    name = "ethresearch"

    def fetch(self, query: ExpandedQuery, days: int, limit: int = 50) -> list[Item]:
        """Fetch topics matching any expansion term from ethresear.ch.

        Iterates through `query.terms`, searches each, and dedupes by topic ID.
        Per-term limits keep the total fetch size bounded regardless of expansion
        breadth.
        """
        terms = query.terms
        per_term_limit = max(limit // max(len(terms), 1), 10)

        seen: dict[int, Item] = {}
        for term in terms:
            topics = self._search_term(term, per_term_limit)
            for topic in topics:
                topic_id = topic["id"]
                if topic_id not in seen:
                    seen[topic_id] = self._build_item(topic)

        return list(seen.values())[:limit]

    def _search_term(self, term: str, limit: int) -> list[dict]:
        params = {
            "q": term,
            "order": "latest",
        }
        headers = {"User-Agent": "agent-skills-digest/1.0"}
        response = httpx.get(SEARCH_URL, params=params, headers=headers, timeout=30.0)
        response.raise_for_status()
        return response.json().get("topics", [])[:limit]

    @staticmethod
    def _engagement(topic: dict) -> int:
        """Composite engagement score.

        Likes are sparse on ethresear.ch so they get a 5x weight.
        Posts (replies) indicate sustained discussion.
        """
        views = topic.get("views", 0)
        likes = topic.get("like_count", 0)
        posts = topic.get("posts_count", 0)
        return views + likes * 5 + posts * 3

    def _build_item(self, topic: dict) -> Item:
        slug = topic.get("slug", "")
        topic_id = topic["id"]
        url = f"{BASE_URL}/t/{slug}/{topic_id}"

        created_at = topic.get("created_at", "")
        if created_at:
            timestamp = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        else:
            timestamp = datetime.now(timezone.utc)

        return Item(
            source=self.name,
            title=topic.get("title") or "",
            url=url,
            author=None,
            timestamp=timestamp,
            engagement=self._engagement(topic),
            raw={
                "topic_id": topic_id,
                "views": topic.get("views", 0),
                "like_count": topic.get("like_count", 0),
                "posts_count": topic.get("posts_count", 0),
                "tags": topic.get("tags", []),
            },
        )
