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


def test_fetch_returns_empty_for_keyless_non_ip_query(monkeypatch):
    """Keyless fetch with a search-term query returns [] -- InternetDB only handles IP lookups."""
    monkeypatch.delenv("SHODAN_API_KEY", raising=False)
    from digest.expansion import ExpandedQuery

    adapter = ShodanAdapter()
    adapter._api_key = ""
    query = ExpandedQuery(original="test", terms=["nginx"])
    assert adapter.fetch(query, days=7) == []


# ----------------------------------------------------------------------
# InternetDB keyless fallback path
# ----------------------------------------------------------------------


def test_is_ip_query_ipv4():
    assert ShodanAdapter._is_ip_query("8.8.8.8") is True


def test_is_ip_query_ipv6():
    assert ShodanAdapter._is_ip_query("2001:4860:4860::8888") is True


def test_is_ip_query_with_whitespace():
    assert ShodanAdapter._is_ip_query("  1.1.1.1  ") is True


def test_is_ip_query_rejects_search_term():
    assert ShodanAdapter._is_ip_query("nginx") is False


def test_is_ip_query_rejects_cidr():
    """CIDR notation should not match -- InternetDB only takes single IPs."""
    assert ShodanAdapter._is_ip_query("10.0.0.0/24") is False


def test_is_ip_query_rejects_partial_ip():
    assert ShodanAdapter._is_ip_query("8.8.8") is False


def test_is_ip_query_handles_empty_string():
    assert ShodanAdapter._is_ip_query("") is False


def test_build_internetdb_item_basic():
    data = {
        "ip": "1.1.1.1",
        "ports": [53, 80, 443],
        "hostnames": ["one.one.one.one"],
        "cpes": ["cpe:/a:cloudflare:cloudflare"],
        "tags": [],
        "vulns": [],
    }
    adapter = ShodanAdapter()
    item = adapter._build_item_from_internetdb(data)
    assert item.raw["kind"] == "internetdb"
    assert item.raw["ip"] == "1.1.1.1"
    assert item.raw["ports"] == [53, 80, 443]
    assert item.url == "https://www.shodan.io/host/1.1.1.1"
    assert "one.one.one.one" in item.title
    assert "3 ports" in item.title
    assert item.author == "one.one.one.one"


def test_build_internetdb_engagement_includes_ports():
    """InternetDB engagement counts ports as exposure signal."""
    data = {"ip": "1.1.1.1", "ports": [53, 80, 443, 2083], "vulns": [], "tags": [], "hostnames": []}
    adapter = ShodanAdapter()
    item = adapter._build_item_from_internetdb(data)
    # 0 vulns + 0 tags + 4 ports = 4
    assert item.engagement == 4


def test_build_internetdb_engagement_with_vulns():
    data = {
        "ip": "1.1.1.1",
        "ports": [80, 443],
        "vulns": ["CVE-2024-1234", "CVE-2024-5678"],
        "tags": ["self-signed"],
        "hostnames": [],
    }
    adapter = ShodanAdapter()
    item = adapter._build_item_from_internetdb(data)
    # 2 vulns * 10 + 1 tag * 5 + 2 ports = 27
    assert item.engagement == 27


def test_build_internetdb_handles_empty_lists():
    """InternetDB returns empty lists for missing data, not nulls -- adapter must not crash."""
    data = {"ip": "1.1.1.1", "ports": [], "vulns": [], "tags": [], "hostnames": [], "cpes": []}
    adapter = ShodanAdapter()
    item = adapter._build_item_from_internetdb(data)
    assert item.engagement == 0
    assert item.author is None


def test_build_internetdb_summary_lists_ports_and_vulns():
    data = {
        "ip": "1.1.1.1",
        "ports": [80, 443, 8080],
        "vulns": ["CVE-2024-1234"],
        "tags": [],
        "hostnames": ["example.com"],
    }
    adapter = ShodanAdapter()
    item = adapter._build_item_from_internetdb(data)
    assert "1.1.1.1" in item.summary
    assert "ports=80,443,8080" in item.summary
    assert "CVE-2024-1234" in item.summary
    assert "example.com" in item.summary


# ----------------------------------------------------------------------
# Facets summary path
# ----------------------------------------------------------------------


def test_build_facet_summary_item_total_is_engagement():
    summary = {
        "total": 12345,
        "facets": {
            "country": [{"value": "US", "count": 5000}, {"value": "DE", "count": 2000}],
            "vuln": [{"value": "CVE-2023-1234", "count": 100}],
        },
    }
    adapter = ShodanAdapter()
    item = adapter._build_facet_summary_item("nginx", summary)
    assert item.engagement == 12345
    assert item.raw["kind"] == "facet_summary"
    assert item.raw["query_term"] == "nginx"


def test_build_facet_summary_title_contains_term_and_total():
    summary = {"total": 1234, "facets": {}}
    item = ShodanAdapter()._build_facet_summary_item("apache", summary)
    assert "apache" in item.title
    assert "1,234" in item.title


def test_build_facet_summary_lists_top_facet_values():
    summary = {
        "total": 999,
        "facets": {
            "country": [{"value": "US", "count": 500}],
            "product": [{"value": "nginx", "count": 200}],
        },
    }
    item = ShodanAdapter()._build_facet_summary_item("test", summary)
    assert "country=US" in item.summary
    assert "product=nginx" in item.summary


def test_build_facet_summary_handles_empty_facets():
    summary = {"total": 0, "facets": {}}
    item = ShodanAdapter()._build_facet_summary_item("nothing", summary)
    assert item.engagement == 0
    assert item.summary == "no facet data"


def test_top_facet_values_filters_malformed_entries():
    """The normalizer should drop entries that don't have both value and count."""
    facets = {
        "country": [
            {"value": "US", "count": 100},
            {"value": "DE"},  # missing count
            {"count": 50},  # missing value
            "not-a-dict",  # wrong type
            {"value": "FR", "count": "20"},  # count as string -- should coerce
        ],
        "not_a_list": "foo",  # whole facet is wrong type
    }
    result = ShodanAdapter._top_facet_values(facets)
    assert result["country"] == [{"value": "US", "count": 100}, {"value": "FR", "count": 20}]
    assert "not_a_list" not in result


def test_facet_summary_item_url_links_to_shodan_search():
    summary = {"total": 1, "facets": {}}
    item = ShodanAdapter()._build_facet_summary_item("nginx", summary)
    assert item.url == "https://www.shodan.io/search?query=nginx"
