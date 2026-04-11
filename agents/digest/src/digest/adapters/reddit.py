"""Reddit adapter via public search JSON API (no OAuth required).

Uses the old.reddit.com JSON endpoints which work without OAuth for read-only
searches. Rate-limited to ~10 req/min without auth -- fine for a digest tool
that runs infrequently. Requires a descriptive User-Agent header (Reddit blocks
default Python user agents).
"""

from __future__ import annotations

from datetime import datetime, timezone

import httpx

from digest.expansion import ExpandedQuery
from digest.models import Item

SEARCH_URL = "https://www.reddit.com/search.json"
USER_AGENT = "digest-agent/0.1 (github.com/DROOdotFOO/agent-skills)"


class RedditAdapter:
    name = "reddit"

    def fetch(self, query: ExpandedQuery, days: int, limit: int = 50) -> list[Item]:
        """Fetch posts matching query terms within a time window.

        Runs one search per term and dedupes by Reddit post ID.
        Uses Reddit's time filter buckets (day/week/month/year) since the
        API doesn't support arbitrary date ranges.
        """
        terms = query.terms
        per_term_limit = max(limit // max(len(terms), 1), 10)
        time_filter = self._days_to_time_filter(days)

        seen: dict[str, Item] = {}
        for term in terms:
            posts = self._search(term, time_filter, per_term_limit)
            for post in posts:
                data = post.get("data", {})
                post_id = data.get("id", "")
                if post_id and post_id not in seen:
                    seen[post_id] = self._build_item(data)

        return list(seen.values())[:limit]

    @staticmethod
    def _days_to_time_filter(days: int) -> str:
        """Map days to Reddit's fixed time filter buckets."""
        if days <= 1:
            return "day"
        if days <= 7:
            return "week"
        if days <= 30:
            return "month"
        if days <= 365:
            return "year"
        return "all"

    def _search(self, term: str, time_filter: str, limit: int) -> list[dict]:
        params = {
            "q": term,
            "sort": "relevance",
            "t": time_filter,
            "limit": min(limit, 100),
            "type": "link",
        }
        headers = {"User-Agent": USER_AGENT}
        response = httpx.get(SEARCH_URL, params=params, headers=headers, timeout=30.0)
        response.raise_for_status()
        data = response.json().get("data", {})
        return data.get("children", [])

    def _build_item(self, post: dict) -> Item:
        score = post.get("score", 0)
        num_comments = post.get("num_comments", 0)
        permalink = post.get("permalink", "")
        return Item(
            source=self.name,
            title=post.get("title", ""),
            url=f"https://reddit.com{permalink}" if permalink else "",
            author=post.get("author"),
            timestamp=datetime.fromtimestamp(post.get("created_utc", 0), tz=timezone.utc),
            engagement=score + num_comments,
            raw={
                "subreddit": post.get("subreddit"),
                "score": score,
                "num_comments": num_comments,
                "link_url": post.get("url"),
            },
        )
