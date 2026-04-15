"""Unit tests for Shodan adapter item building and engagement scoring."""

from __future__ import annotations

from digest.adapters.shodan import ShodanAdapter


def _build(match: dict, query_term: str = "test") -> dict:
    """Build an Item from a Shodan match dict and return key fields."""
    adapter = ShodanAdapter()
    item = adapter._build_item(match, query_term)
    if item is None:
        return {}
    return {
        "engagement": item.engagement,
        "raw": item.raw,
        "url": item.url,
        "title": item.title,
        "summary": item.summary,
        "author": item.author,
    }


def test_basic_item_building():
    match = {
        "ip_str": "1.2.3.4",
        "port": 443,
        "org": "Acme Corp",
        "product": "nginx",
        "version": "1.25.0",
        "timestamp": "2026-04-10T12:00:00+00:00",
        "location": {"country_code": "US", "city": "Austin"},
    }
    result = _build(match)
    assert result["url"] == "https://www.shodan.io/host/1.2.3.4"
    assert "1.2.3.4:443" in result["title"]
    assert "nginx/1.25.0" in result["title"]
    assert "(Acme Corp)" in result["title"]
    assert result["author"] == "Acme Corp"
    assert result["raw"]["port"] == 443
    assert result["raw"]["country_code"] == "US"


def test_engagement_from_vulns():
    match = {
        "ip_str": "5.6.7.8",
        "port": 80,
        "org": "Test",
        "vulns": ["CVE-2024-1234", "CVE-2024-5678"],
        "tags": ["cloud"],
        "timestamp": "2026-04-10T12:00:00+00:00",
        "location": {},
    }
    result = _build(match)
    # 2 vulns * 10 + 1 tag * 5 + 1 port = 26
    assert result["engagement"] == 26


def test_engagement_no_vulns_no_tags():
    match = {
        "ip_str": "10.0.0.1",
        "port": 22,
        "org": "Unknown",
        "timestamp": "2026-04-10T12:00:00+00:00",
        "location": {},
    }
    result = _build(match)
    # 0 vulns + 0 tags + 1 port = 1
    assert result["engagement"] == 1


def test_empty_ip_returns_none():
    match = {"ip_str": "", "port": 80, "timestamp": "2026-04-10T12:00:00+00:00", "location": {}}
    adapter = ShodanAdapter()
    assert adapter._build_item(match, "test") is None


def test_summary_includes_query_term():
    match = {
        "ip_str": "9.8.7.6",
        "port": 8080,
        "org": "Example",
        "product": "Apache",
        "vulns": ["CVE-2023-0001"],
        "timestamp": "2026-04-10T12:00:00+00:00",
        "location": {"country_code": "DE", "city": "Berlin"},
    }
    result = _build(match, query_term="apache vulnerable")
    assert result["summary"].startswith("[apache vulnerable]")
    assert "org=Example" in result["summary"]
    assert "country=DE" in result["summary"]
    assert "CVE-2023-0001" in result["summary"]
    assert "running=Apache" in result["summary"]


def test_url_points_to_shodan_host():
    match = {
        "ip_str": "192.168.1.1",
        "port": 443,
        "org": "Private",
        "timestamp": "2026-04-10T12:00:00+00:00",
        "location": {},
    }
    result = _build(match)
    assert result["url"] == "https://www.shodan.io/host/192.168.1.1"


def test_missing_optional_fields():
    """Adapter handles matches with minimal fields gracefully."""
    match = {
        "ip_str": "10.10.10.10",
        "port": 9200,
        "timestamp": "2026-04-10T12:00:00+00:00",
        "location": {},
    }
    result = _build(match)
    assert result["raw"]["org"] == "Unknown"
    assert result["raw"]["product"] == ""
    assert result["raw"]["asn"] == ""
    assert "10.10.10.10:9200" in result["title"]


def test_fetch_returns_empty_without_api_key(monkeypatch):
    """fetch() returns empty list when SHODAN_API_KEY is not set."""
    monkeypatch.delenv("SHODAN_API_KEY", raising=False)
    from digest.expansion import ExpandedQuery

    adapter = ShodanAdapter()
    adapter._api_key = ""
    query = ExpandedQuery(original="test", terms=["test"])
    assert adapter.fetch(query, days=7) == []
