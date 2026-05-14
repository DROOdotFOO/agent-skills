"""Shodan adapter -- main search API plus InternetDB fallback and facets summary.

Three pathways:

1. **/shodan/host/search** (requires `SHODAN_API_KEY`, costs query credits) --
   the original per-host search. Returns one Item per matched banner.

2. **InternetDB fallback** (keyless, free) -- when no API key is set and a
   query term looks like an IP address, fetch the InternetDB record at
   `internetdb.shodan.io/{ip}`. Updated weekly so it's stale vs main API,
   but available without auth.

3. **Facets summary** (requires key but costs ZERO query credits) -- after
   the per-host search succeeds, also call `/shodan/host/count` with facets
   to surface aggregate exposure stats (top products, top countries, top
   vulns). Emitted as a single aggregate Item alongside per-host items.

Engagement scoring: facet count (total results for a facet value) serves as
the primary signal -- a high count means many exposed hosts matching the
query, which is the security-relevant metric.
"""

from __future__ import annotations

import ipaddress
import os
from datetime import datetime, timezone

from digest.adapters._helpers import coerce_int, fetch_json, parse_iso_utc
from digest.expansion import ExpandedQuery
from digest.models import Item

API_BASE = "https://api.shodan.io"
INTERNETDB_URL = "https://internetdb.shodan.io"

# Facets requested on every /shodan/host/count call. Capping each at top-10
# values keeps the response small. None of these consume query credits.
DEFAULT_FACETS = "org:10,country:10,port:10,vuln:10,product:10"


class ShodanAdapter:
    name = "shodan"

    def __init__(self) -> None:
        self._api_key = os.environ.get("SHODAN_API_KEY", "")

    def fetch(self, query: ExpandedQuery, days: int, limit: int = 50) -> list[Item]:
        """Fetch Shodan results matching the query terms.

        With a key: per-host search via /shodan/host/search, plus one aggregate
        facets Item per term.
        Without a key: IP-shaped query terms route to InternetDB; everything
        else returns nothing (keyless search is not available).
        """
        terms = query.terms
        if not terms:
            return []

        if not self._api_key:
            return self._fetch_keyless(terms, limit)

        return self._fetch_authenticated(terms, limit)

    # ------------------------------------------------------------------
    # Authenticated path: /shodan/host/search + facets summary
    # ------------------------------------------------------------------

    def _fetch_authenticated(self, terms: list[str], limit: int) -> list[Item]:
        per_term_limit = max(limit // max(len(terms), 1), 10)
        seen: dict[str, Item] = {}
        extras: list[Item] = []

        for term in terms:
            for match in self._search(term, per_term_limit):
                ip = match.get("ip_str", "")
                if ip and ip not in seen:
                    item = self._build_item(match, term)
                    if item is not None:
                        seen[ip] = item

            summary = self._facet_summary(term)
            if summary is not None:
                extras.append(self._build_facet_summary_item(term, summary))

        return (list(seen.values()) + extras)[:limit]

    def _search(self, term: str, limit: int) -> list[dict]:
        params = {"key": self._api_key, "query": term, "page": 1}
        payload = fetch_json(f"{API_BASE}/shodan/host/search", params=params, default={})
        return (payload.get("matches") or [])[:limit]

    def _facet_summary(self, term: str) -> dict | None:
        """Call /shodan/host/count -- free, zero query credits, returns facets."""
        params = {"key": self._api_key, "query": term, "facets": DEFAULT_FACETS}
        return fetch_json(f"{API_BASE}/shodan/host/count", params=params, default=None)

    def _build_facet_summary_item(self, term: str, summary: dict) -> Item:
        total = coerce_int(summary.get("total"))
        facets = summary.get("facets") or {}
        top = self._top_facet_values(facets)

        title = f"Shodan facets: {term} -- {total:,} hosts"
        bits = []
        for facet_name, values in top.items():
            if not values:
                continue
            head = values[0]
            bits.append(f"{facet_name}={head['value']} ({head['count']:,})")
        summary_line = " | ".join(bits) if bits else "no facet data"

        return Item(
            source=self.name,
            title=title,
            url=f"https://www.shodan.io/search?query={term}",
            author=None,
            timestamp=datetime.now(timezone.utc),
            engagement=total,
            summary=summary_line,
            raw={
                "kind": "facet_summary",
                "query_term": term,
                "total": total,
                "facets": facets,
            },
        )

    # ------------------------------------------------------------------
    # Keyless path: InternetDB lookups for IP-shaped query terms
    # ------------------------------------------------------------------

    def _fetch_keyless(self, terms: list[str], limit: int) -> list[Item]:
        seen: dict[str, Item] = {}
        for term in terms:
            if not self._is_ip_query(term):
                continue
            data = self._lookup_internetdb(term)
            if data is None:
                continue
            ip = data.get("ip") or term
            if ip in seen:
                continue
            seen[ip] = self._build_item_from_internetdb(data)
            if len(seen) >= limit:
                break
        return list(seen.values())

    def _lookup_internetdb(self, ip: str) -> dict | None:
        # InternetDB returns 404 for IPs with no data; fetch_json returns the
        # default (None) for any non-2xx response, so 404 is handled implicitly.
        return fetch_json(f"{INTERNETDB_URL}/{ip}", default=None, timeout=15.0)

    def _build_item_from_internetdb(self, data: dict) -> Item:
        ip = data.get("ip", "")
        ports = data.get("ports") or []
        vulns = data.get("vulns") or []
        tags = data.get("tags") or []
        cpes = data.get("cpes") or []
        hostnames = data.get("hostnames") or []

        # Engagement: same scoring shape as the main path for consistency.
        # Per-host search uses len(vulns)*10 + len(tags)*5 + 1; InternetDB
        # adds ports as a coarse exposure signal since per-host search returns
        # one item per port (so port count is implicit there but explicit here).
        engagement = len(vulns) * 10 + len(tags) * 5 + len(ports)

        title_parts = [ip]
        if hostnames:
            title_parts.append(f"({hostnames[0]})")
        if ports:
            title_parts.append(f"{len(ports)} ports")

        return Item(
            source=self.name,
            title=" ".join(title_parts),
            url=f"https://www.shodan.io/host/{ip}",
            author=hostnames[0] if hostnames else None,
            timestamp=datetime.now(timezone.utc),
            engagement=engagement,
            summary=self._build_internetdb_summary(ip, ports, vulns, hostnames),
            raw={
                "kind": "internetdb",
                "ip": ip,
                "ports": ports,
                "vulns": vulns,
                "tags": tags,
                "cpes": cpes,
                "hostnames": hostnames,
            },
        )

    @staticmethod
    def _build_internetdb_summary(
        ip: str,
        ports: list[int],
        vulns: list[str],
        hostnames: list[str],
    ) -> str:
        parts = [ip]
        if hostnames:
            parts.append(f"hostnames={','.join(hostnames[:3])}")
        if ports:
            parts.append(f"ports={','.join(str(p) for p in ports[:8])}")
        if vulns:
            parts.append(f"vulns={','.join(vulns[:5])}")
        return " | ".join(parts)

    # ------------------------------------------------------------------
    # Authenticated per-host Item builder (unchanged behavior)
    # ------------------------------------------------------------------

    def _build_item(self, match: dict, query_term: str) -> Item | None:
        ip = match.get("ip_str", "")
        port = match.get("port", 0)
        if not ip:
            return None

        timestamp = parse_iso_utc(match.get("timestamp")) or datetime.now(timezone.utc)

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
                "kind": "host",
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

    # ------------------------------------------------------------------
    # Small helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_ip_query(term: str) -> bool:
        """True iff `term` parses as a single IPv4 or IPv6 address."""
        try:
            ipaddress.ip_address(term.strip())
        except (ValueError, AttributeError):
            return False
        return True

    @staticmethod
    def _top_facet_values(facets: dict) -> dict[str, list[dict]]:
        """Normalize facets to {facet_name: [{count, value}, ...]} regardless of API quirks."""
        result: dict[str, list[dict]] = {}
        for facet_name, values in facets.items():
            if not isinstance(values, list):
                continue
            normalized: list[dict] = []
            for v in values:
                if isinstance(v, dict) and "value" in v and "count" in v:
                    normalized.append({"value": v["value"], "count": int(v["count"])})
            result[facet_name] = normalized
        return result
