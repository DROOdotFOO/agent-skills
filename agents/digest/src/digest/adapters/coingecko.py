"""CoinGecko adapter -- trending tokens, top gainers/losers, and new listings."""

from __future__ import annotations

from datetime import datetime, timezone

import httpx

from digest.expansion import ExpandedQuery
from digest.models import Item

BASE_URL = "https://api.coingecko.com/api/v3"


class CoinGeckoAdapter:
    name = "coingecko"

    def fetch(self, query: ExpandedQuery, days: int, limit: int = 50) -> list[Item]:
        """Fetch trending tokens, top gainers/losers, and new listings.

        CoinGecko doesn't have a text search API, so we fetch market movers
        and filter by query terms in title/symbol. For broad topics like
        "crypto" or "defi", most items will match.
        """
        items: list[Item] = []
        terms_lower = [t.lower() for t in query.terms]

        items.extend(self._fetch_trending(terms_lower, limit // 3))
        items.extend(self._fetch_gainers_losers(terms_lower, limit // 3))

        if days <= 7:
            items.extend(self._fetch_new_coins(terms_lower, limit // 3))

        return items[:limit]

    def _matches_terms(self, name: str, symbol: str, terms: list[str]) -> bool:
        """Check if a coin matches any of the search terms."""
        if not terms:
            return True
        name_lower = name.lower()
        symbol_lower = symbol.lower()
        for term in terms:
            t = term.lower()
            if t in name_lower or t in symbol_lower:
                return True
            if t in ("crypto", "defi", "token", "coin", "market"):
                return True
        return False

    def _fetch_trending(self, terms: list[str], limit: int) -> list[Item]:
        """Fetch trending coins from CoinGecko."""
        try:
            resp = httpx.get(
                f"{BASE_URL}/search/trending",
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
        except (httpx.HTTPError, ValueError):
            return []

        items = []
        for entry in data.get("coins", [])[:limit]:
            coin = entry.get("item", {})
            name = coin.get("name", "")
            symbol = coin.get("symbol", "")

            if not self._matches_terms(name, symbol, terms):
                continue

            market_cap_rank = coin.get("market_cap_rank") or 9999
            score = coin.get("score", 0)
            engagement = max(1000 - (market_cap_rank * 10), 0) + (100 - score * 10)

            items.append(
                Item(
                    source=self.name,
                    title=f"[Trending] {name} ({symbol.upper()})",
                    url=f"https://www.coingecko.com/en/coins/{coin.get('id', '')}",
                    timestamp=datetime.now(timezone.utc),
                    engagement=max(engagement, 1),
                    raw={
                        "coin_id": coin.get("id"),
                        "symbol": symbol,
                        "market_cap_rank": market_cap_rank,
                        "price_btc": coin.get("price_btc"),
                        "type": "trending",
                    },
                )
            )

        return items

    def _fetch_gainers_losers(self, terms: list[str], limit: int) -> list[Item]:
        """Fetch top gainers and losers."""
        try:
            resp = httpx.get(
                f"{BASE_URL}/coins/top_gainers_losers",
                params={"vs_currency": "usd", "duration": "24h"},
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
        except (httpx.HTTPError, ValueError):
            return []

        items = []
        for category in ("top_gainers", "top_losers"):
            label = "Gainer" if category == "top_gainers" else "Loser"
            for coin in data.get(category, [])[:limit]:
                name = coin.get("name", "")
                symbol = coin.get("symbol", "")

                if not self._matches_terms(name, symbol, terms):
                    continue

                change = coin.get("usd_24h_change", 0) or 0
                volume = coin.get("usd_24h_vol", 0) or 0
                engagement = int(abs(change) * 10 + min(volume / 1_000_000, 500))

                items.append(
                    Item(
                        source=self.name,
                        title=f"[{label} {change:+.1f}%] {name} ({symbol.upper()})",
                        url=f"https://www.coingecko.com/en/coins/{coin.get('id', '')}",
                        timestamp=datetime.now(timezone.utc),
                        engagement=max(engagement, 1),
                        raw={
                            "coin_id": coin.get("id"),
                            "symbol": symbol,
                            "price_usd": coin.get("usd"),
                            "change_24h": change,
                            "volume_24h": volume,
                            "type": category,
                        },
                    )
                )

        return items

    def _fetch_new_coins(self, terms: list[str], limit: int) -> list[Item]:
        """Fetch recently listed coins."""
        try:
            resp = httpx.get(
                f"{BASE_URL}/coins/list/new",
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
        except (httpx.HTTPError, ValueError):
            return []

        items = []
        for coin in data[: limit * 2]:
            name = coin.get("name", "")
            symbol = coin.get("symbol", "")

            if not self._matches_terms(name, symbol, terms):
                continue

            activated = coin.get("activated_at", 0)
            ts = (
                datetime.fromtimestamp(activated, tz=timezone.utc)
                if activated
                else datetime.now(timezone.utc)
            )

            items.append(
                Item(
                    source=self.name,
                    title=f"[New Listing] {name} ({symbol.upper()})",
                    url=f"https://www.coingecko.com/en/coins/{coin.get('id', '')}",
                    timestamp=ts,
                    engagement=50,
                    raw={
                        "coin_id": coin.get("id"),
                        "symbol": symbol,
                        "activated_at": activated,
                        "type": "new_listing",
                    },
                )
            )

            if len(items) >= limit:
                break

        return items
