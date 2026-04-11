"""Package registry adapter for hex.pm, crates.io, and npm (no auth required).

Searches across all three registries for each query term and deduplicates
by (registry, package_name). All three APIs are free and unauthenticated,
though crates.io requires a descriptive User-Agent header.
"""

from __future__ import annotations

from datetime import datetime, timezone

import httpx

from digest.expansion import ExpandedQuery
from digest.models import Item

HEX_URL = "https://hex.pm/api/packages"
CRATES_URL = "https://crates.io/api/v1/crates"
NPM_URL = "https://registry.npmjs.org/-/v1/search"
USER_AGENT = "digest-agent/0.1 (github.com/DROOdotFOO/agent-skills)"

# npm doesn't expose download counts in search results, so we approximate
# engagement from the popularity score (0.0-1.0) scaled to a comparable range.
NPM_POPULARITY_SCALE = 10000


class PackagesAdapter:
    name = "packages"

    def fetch(self, query: ExpandedQuery, days: int, limit: int = 50) -> list[Item]:
        """Fetch packages matching query terms across hex.pm, crates.io, and npm.

        Runs one search per term per registry and dedupes by (registry, name).
        """
        terms = query.terms
        per_term_limit = max(limit // max(len(terms), 1), 10)

        seen: dict[str, Item] = {}
        for term in terms:
            for search_fn in (self._search_hex, self._search_crates, self._search_npm):
                packages = search_fn(term, per_term_limit)
                for pkg in packages:
                    key = f"{pkg['registry']}:{pkg['name']}"
                    if key not in seen:
                        seen[key] = self._build_item(pkg)

        return list(seen.values())[:limit]

    def _search_hex(self, term: str, limit: int) -> list[dict]:
        params = {"search": term, "sort": "recent_downloads", "page": 1}
        response = httpx.get(HEX_URL, params=params, timeout=30.0)
        response.raise_for_status()
        results = []
        for pkg in response.json()[:limit]:
            releases = pkg.get("releases", [])
            latest_release = releases[0] if releases else {}
            results.append(
                {
                    "registry": "hex",
                    "name": pkg.get("name", ""),
                    "description": (pkg.get("meta") or {}).get("description", ""),
                    "url": pkg.get("url", f"https://hex.pm/packages/{pkg.get('name', '')}"),
                    "downloads": (pkg.get("downloads") or {}).get("recent", 0),
                    "version": latest_release.get("version"),
                    "updated_at": latest_release.get("inserted_at"),
                    "author": None,
                }
            )
        return results

    def _search_crates(self, term: str, limit: int) -> list[dict]:
        params = {"q": term, "sort": "recent-downloads", "per_page": min(limit, 100)}
        headers = {"User-Agent": USER_AGENT}
        response = httpx.get(CRATES_URL, params=params, headers=headers, timeout=30.0)
        response.raise_for_status()
        results = []
        for crate in response.json().get("crates", []):
            results.append(
                {
                    "registry": "crates",
                    "name": crate.get("name", ""),
                    "description": crate.get("description", ""),
                    "url": f"https://crates.io/crates/{crate.get('name', '')}",
                    "downloads": crate.get("recent_downloads", 0),
                    "version": crate.get("newest_version"),
                    "updated_at": crate.get("updated_at"),
                    "author": None,
                }
            )
        return results

    def _search_npm(self, term: str, limit: int) -> list[dict]:
        params = {"text": term, "size": min(limit, 250)}
        response = httpx.get(NPM_URL, params=params, timeout=30.0)
        response.raise_for_status()
        results = []
        for obj in response.json().get("objects", []):
            package = obj.get("package", {})
            score = obj.get("score", {})
            popularity = (score.get("detail") or {}).get("popularity", 0.0)
            links = package.get("links", {})
            publisher = package.get("publisher", {})
            results.append(
                {
                    "registry": "npm",
                    "name": package.get("name", ""),
                    "description": package.get("description", ""),
                    "url": links.get(
                        "npm", f"https://www.npmjs.com/package/{package.get('name', '')}"
                    ),
                    "downloads": int(popularity * NPM_POPULARITY_SCALE),
                    "version": package.get("version"),
                    "updated_at": package.get("date"),
                    "author": publisher.get("username"),
                }
            )
        return results

    def _build_item(self, pkg: dict) -> Item:
        timestamp = _parse_timestamp(pkg.get("updated_at"))
        return Item(
            source=self.name,
            title=f"[{pkg['registry']}] {pkg['name']}",
            url=pkg.get("url", ""),
            author=pkg.get("author"),
            timestamp=timestamp,
            engagement=pkg.get("downloads", 0),
            summary=pkg.get("description"),
            raw={
                "registry": pkg["registry"],
                "downloads": pkg.get("downloads", 0),
                "version": pkg.get("version"),
            },
        )


def _parse_timestamp(value: str | None) -> datetime:
    """Parse an ISO 8601 timestamp, falling back to epoch on failure."""
    if not value:
        return datetime.fromtimestamp(0, tz=timezone.utc)
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return datetime.fromtimestamp(0, tz=timezone.utc)
