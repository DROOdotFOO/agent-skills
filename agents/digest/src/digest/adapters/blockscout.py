"""Blockscout adapter -- on-chain activity via Blockscout API v2 (no auth)."""

from __future__ import annotations

from datetime import datetime, timezone

import httpx

from digest.expansion import ExpandedQuery
from digest.models import Item

BLOCKSCOUT_URLS: dict[int, str] = {
    1: "https://eth.blockscout.com",
    137: "https://polygon.blockscout.com",
    10: "https://optimism.blockscout.com",
    42161: "https://arbitrum.blockscout.com",
    8453: "https://base.blockscout.com",
    100: "https://gnosis.blockscout.com",
    324: "https://zksync.blockscout.com",
    534352: "https://scroll.blockscout.com",
}

# Default chain for digest queries
DEFAULT_CHAIN = 1


class BlockscoutAdapter:
    name = "blockscout"

    def fetch(self, query: ExpandedQuery, days: int, limit: int = 50) -> list[Item]:
        """Fetch on-chain activity matching the query.

        Searches for token transfers and address activity. Uses the Blockscout
        search API to find addresses/tokens matching query terms. Distributes
        limit across terms, capped at 3 terms to avoid excessive API calls.
        """
        terms = query.terms
        per_term_limit = max(limit // max(len(terms[:3]), 1), 10)
        items: list[Item] = []

        for term in terms[:3]:
            items.extend(self._search_and_fetch(term, per_term_limit))

        seen_urls: set[str] = set()
        deduped: list[Item] = []
        for item in items:
            if item.url not in seen_urls:
                seen_urls.add(item.url)
                deduped.append(item)

        return deduped[:limit]

    def _search_and_fetch(self, term: str, limit: int) -> list[Item]:
        """Search Blockscout for tokens/addresses and fetch recent activity."""
        base_url = BLOCKSCOUT_URLS[DEFAULT_CHAIN]
        items: list[Item] = []

        try:
            resp = httpx.get(
                f"{base_url}/api/v2/search",
                params={"q": term},
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
        except (httpx.HTTPError, ValueError):
            return []

        results = data.get("items", [])[:5]
        per_result_limit = max(limit // max(len(results), 1), 5)
        for result in results:
            result_type = result.get("type", "")

            if result_type == "token":
                items.extend(self._fetch_token_transfers(base_url, result, per_result_limit))
            elif result_type == "address":
                items.extend(self._fetch_address_txs(base_url, result, per_result_limit))

        return items

    def _fetch_token_transfers(self, base_url: str, token: dict, limit: int) -> list[Item]:
        """Fetch recent transfers for a token."""
        address = token.get("address", "")
        name = token.get("name", "") or address[:10]
        symbol = token.get("symbol", "")

        try:
            resp = httpx.get(
                f"{base_url}/api/v2/tokens/{address}/transfers",
                params={"limit": str(min(limit, 20))},
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
        except (httpx.HTTPError, ValueError):
            return []

        return [
            self._build_transfer_item(tx, base_url, name, symbol)
            for tx in data.get("items", [])[:limit]
        ]

    def _build_transfer_item(self, tx: dict, base_url: str, name: str, symbol: str) -> Item:
        value = tx.get("total", {}).get("value", "0")
        decimals = int(tx.get("total", {}).get("decimals", "18") or "18")
        amount = int(value) / (10**decimals) if value else 0
        engagement = min(int(amount), 10000) if amount > 0 else 1

        ts = _parse_timestamp(tx.get("timestamp", ""))
        tx_hash = tx.get("tx_hash", "")

        return Item(
            source=self.name,
            title=f"[Transfer] {amount:.2f} {symbol} ({name})",
            url=f"{base_url}/tx/{tx_hash}",
            timestamp=ts,
            engagement=engagement,
            raw={
                "tx_hash": tx_hash,
                "token": symbol,
                "amount": amount,
                "from": _addr(tx.get("from")),
                "to": _addr(tx.get("to")),
                "type": "token_transfer",
            },
        )

    def _fetch_address_txs(self, base_url: str, address_info: dict, limit: int) -> list[Item]:
        """Fetch recent transactions for an address."""
        address = address_info.get("address", "")
        name = address_info.get("name", "") or address[:10]

        try:
            resp = httpx.get(
                f"{base_url}/api/v2/addresses/{address}/transactions",
                params={"limit": str(min(limit, 20))},
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
        except (httpx.HTTPError, ValueError):
            return []

        return [self._build_tx_item(tx, base_url, name) for tx in data.get("items", [])[:limit]]

    def _build_tx_item(self, tx: dict, base_url: str, name: str) -> Item:
        value_wei = int(tx.get("value", "0"))
        value_eth = value_wei / 1e18
        engagement = min(int(value_eth * 100), 10000) if value_eth > 0 else 1

        ts = _parse_timestamp(tx.get("timestamp", ""))
        tx_hash = tx.get("hash", "")
        method = tx.get("method") or "transfer"

        return Item(
            source=self.name,
            title=f"[{method}] {value_eth:.4f} ETH ({name})",
            url=f"{base_url}/tx/{tx_hash}",
            timestamp=ts,
            engagement=engagement,
            raw={
                "tx_hash": tx_hash,
                "value_eth": value_eth,
                "method": method,
                "from": _addr(tx.get("from")),
                "to": _addr(tx.get("to")),
                "type": "transaction",
            },
        )


def _parse_timestamp(ts_str: str) -> datetime:
    """Parse a Blockscout API timestamp."""
    if ts_str:
        try:
            return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def _addr(val: str | dict | None) -> str:
    """Extract address string from Blockscout's address field (may be dict or str)."""
    if isinstance(val, dict):
        return val.get("hash", "")
    return val or ""
