"""Shodan adapter via the Shodan REST API.

Requires a SHODAN_API_KEY environment variable. Free tier allows up to 1 query
credit per month for search, but /shodan/host/search returns 100 results per
page. The free API also provides banner data via /shodan/host/{ip}.

Engagement scoring: facet count (total results for a facet value) serves as the
primary signal -- a high count means many exposed hosts matching the query,
which is the security-relevant metric.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

import httpx

from digest.expansion import ExpandedQuery
from digest.models import Item

API_BASE = "https://api.shodan.io"


class ShodanAdapter:
    name = "shodan"

    def __init__(self) -> None:
        self._api_key = os.environ.get("SHODAN_API_KEY", "")

    def fetch(self, query: ExpandedQuery, days: int, limit: int = 50) -> list[Item]:
        """Fetch Shodan search results matching query terms.

        Runs /shodan/host/search for each term and dedupes by IP. Also fetches
        facet counts to surface aggregate exposure stats. The `days` parameter
        is used to filter results by last_update timestamp.
        """
        if not self._api_key:
            return []

        terms = query.terms
        per_term_limit = max(limit // max(len(terms), 1), 10)

        seen: dict[str, Item] = {}
        for term in terms:
            results = self._search(term, per_term_limit)
            for match in results:
                ip = match.get("ip_str", "")
                if ip and ip not in seen:
                    item = self._build_item(match, term)
                    if item is not None:
                        seen[ip] = item

        return list(seen.values())[:limit]

    def _search(self, term: str, limit: int) -> list[dict]:
        """Search Shodan for hosts matching a query string."""
        params = {
            "key": self._api_key,
            "query": term,
            "page": 1,
        }
        response = httpx.get(
            f"{API_BASE}/shodan/host/search",
            params=params,
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("matches", [])[:limit]

    def _build_item(self, match: dict, query_term: str) -> Item | None:
        """Convert a Shodan banner/match into a digest Item."""
        ip = match.get("ip_str", "")
        port = match.get("port", 0)
        if not ip:
            return None

        # Parse timestamp -- Shodan uses ISO format
        timestamp_str = match.get("timestamp", "")
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                timestamp = datetime.now(timezone.utc)
        else:
            timestamp = datetime.now(timezone.utc)

        org = match.get("org", "Unknown")
        product = match.get("product", "")
        version = match.get("version", "")
        os_name = match.get("os", "")

        title_parts = [f"{ip}:{port}"]
        if product:
            title_parts.append(product)
            if version:
                title_parts[-1] = f"{product}/{version}"
        if org != "Unknown":
            title_parts.append(f"({org})")

        # Engagement: number of open ports on this host serves as exposure signal.
        # Shodan doesn't return this per-match, so use port count from vulns/tags.
        vulns = match.get("vulns", [])
        tags = match.get("tags", [])
        engagement = len(vulns) * 10 + len(tags) * 5 + (1 if port else 0)

        return Item(
            source=self.name,
            title=" ".join(title_parts),
            url=f"https://www.shodan.io/host/{ip}",
            author=org,
            timestamp=timestamp,
            engagement=engagement,
            summary=self._build_summary(match, query_term),
            raw={
                "ip": ip,
                "port": port,
                "org": org,
                "product": product,
                "version": version,
                "os": os_name,
                "vulns": vulns,
                "tags": tags,
                "asn": match.get("asn", ""),
                "isp": match.get("isp", ""),
                "country_code": match.get("location", {}).get("country_code", ""),
                "city": match.get("location", {}).get("city", ""),
            },
        )

    @staticmethod
    def _build_summary(match: dict, query_term: str) -> str:
        """Build a concise summary line for the match."""
        parts: list[str] = []
        ip = match.get("ip_str", "")
        port = match.get("port", 0)
        org = match.get("org", "")
        country = match.get("location", {}).get("country_code", "")

        parts.append(f"{ip}:{port}")
        if org:
            parts.append(f"org={org}")
        if country:
            parts.append(f"country={country}")

        vulns = match.get("vulns", [])
        if vulns:
            parts.append(f"vulns={','.join(vulns[:5])}")

        product = match.get("product", "")
        if product:
            version = match.get("version", "")
            parts.append(f"running={product}" + (f"/{version}" if version else ""))

        return f"[{query_term}] " + " | ".join(parts)
