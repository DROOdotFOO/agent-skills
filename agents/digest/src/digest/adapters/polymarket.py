"""Polymarket adapter via the Gamma API (no auth required).

Fetches active prediction markets and filters client-side by search terms
matching the market question or description.
"""

from __future__ import annotations

from datetime import datetime, timezone

import httpx

from digest.expansion import ExpandedQuery
from digest.models import Item

GAMMA_URL = "https://gamma-api.polymarket.com/markets"


class PolymarketAdapter:
    name = "polymarket"

    def fetch(self, query: ExpandedQuery, days: int, limit: int = 50) -> list[Item]:
        """Fetch active markets matching any query term.

        Pulls active/open markets from the Gamma API and filters client-side
        by checking if any term appears in the market question or description.
        Dedupes by question text (markets don't have a stable external ID).
        """
        terms = query.terms
        markets = self._fetch_markets(limit=200)

        seen: dict[str, Item] = {}
        for market in markets:
            question = market.get("question", "")
            description = market.get("description", "")
            searchable = f"{question} {description}".lower()

            if any(term.lower() in searchable for term in terms):
                key = question.lower().strip()
                if key and key not in seen:
                    seen[key] = self._build_item(market)

        return list(seen.values())[:limit]

    def _fetch_markets(self, limit: int) -> list[dict]:
        params = {
            "limit": min(limit, 200),
            "active": "true",
            "closed": "false",
        }
        response = httpx.get(GAMMA_URL, params=params, timeout=30.0)
        response.raise_for_status()
        return response.json()

    def _build_item(self, market: dict) -> Item:
        question = market.get("question", "")
        volume = self._parse_volume(market.get("volume"))
        liquidity = self._parse_volume(market.get("liquidity"))

        outcomes = market.get("outcomes", "")
        outcome_prices = market.get("outcomePrices", "")

        # Construct a URL from the condition_id or slug if available,
        # otherwise fall back to the main site.
        slug = market.get("slug", "")
        url = f"https://polymarket.com/event/{slug}" if slug else "https://polymarket.com"

        end_date = market.get("endDate")
        timestamp = self._parse_timestamp(end_date) or datetime.now(timezone.utc)

        return Item(
            source=self.name,
            title=question,
            url=url,
            author=None,
            timestamp=timestamp,
            engagement=volume,
            raw={
                "volume": volume,
                "liquidity": liquidity,
                "outcomes": outcomes,
                "outcome_prices": outcome_prices,
                "end_date": end_date,
                "active": market.get("active"),
                "closed": market.get("closed"),
            },
        )

    @staticmethod
    def _parse_volume(value: str | float | int | None) -> int:
        """Parse volume/liquidity to an integer dollar amount."""
        if value is None:
            return 0
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def _parse_timestamp(value: str | None) -> datetime | None:
        """Parse an ISO 8601 timestamp string."""
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
