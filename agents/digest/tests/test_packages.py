"""Unit tests for packages adapter engagement formulas and item building."""

from __future__ import annotations

from digest.adapters.packages import NPM_POPULARITY_SCALE, PackagesAdapter


def _build(pkg: dict) -> dict:
    """Build an Item from a normalized package dict and return key fields."""
    adapter = PackagesAdapter()
    item = adapter._build_item(pkg)
    return {
        "engagement": item.engagement,
        "raw": item.raw,
        "url": item.url,
        "title": item.title,
        "author": item.author,
        "summary": item.summary,
    }


# -- Engagement (downloads-based) --


def test_hex_engagement_uses_recent_downloads():
    pkg = {
        "registry": "hex",
        "name": "phoenix",
        "downloads": 45000,
        "url": "https://hex.pm/packages/phoenix",
        "version": "1.7.0",
    }
    result = _build(pkg)
    assert result["engagement"] == 45000


def test_crates_engagement_uses_recent_downloads():
    pkg = {
        "registry": "crates",
        "name": "serde",
        "downloads": 120000,
        "url": "https://crates.io/crates/serde",
        "version": "1.0.200",
    }
    result = _build(pkg)
    assert result["engagement"] == 120000


def test_npm_engagement_uses_scaled_popularity():
    popularity = 0.85
    expected = int(popularity * NPM_POPULARITY_SCALE)
    pkg = {
        "registry": "npm",
        "name": "zod",
        "downloads": expected,
        "url": "https://www.npmjs.com/package/zod",
        "version": "3.22.0",
    }
    result = _build(pkg)
    assert result["engagement"] == expected


def test_zero_downloads_gives_zero_engagement():
    pkg = {
        "registry": "hex",
        "name": "unknown",
        "downloads": 0,
        "url": "https://hex.pm/packages/unknown",
    }
    result = _build(pkg)
    assert result["engagement"] == 0


# -- Item building --


def test_title_includes_registry_prefix():
    pkg = {
        "registry": "crates",
        "name": "tokio",
        "downloads": 100,
        "url": "https://crates.io/crates/tokio",
    }
    result = _build(pkg)
    assert result["title"] == "[crates] tokio"


def test_raw_includes_registry_and_version():
    pkg = {
        "registry": "npm",
        "name": "express",
        "downloads": 5000,
        "url": "https://www.npmjs.com/package/express",
        "version": "4.18.2",
    }
    result = _build(pkg)
    assert result["raw"]["registry"] == "npm"
    assert result["raw"]["version"] == "4.18.2"
    assert result["raw"]["downloads"] == 5000


def test_author_preserved_when_present():
    pkg = {
        "registry": "npm",
        "name": "zod",
        "downloads": 100,
        "url": "https://www.npmjs.com/package/zod",
        "author": "colinhacks",
    }
    result = _build(pkg)
    assert result["author"] == "colinhacks"


def test_author_none_when_absent():
    pkg = {
        "registry": "hex",
        "name": "ecto",
        "downloads": 100,
        "url": "https://hex.pm/packages/ecto",
    }
    result = _build(pkg)
    assert result["author"] is None


def test_description_in_summary():
    pkg = {
        "registry": "crates",
        "name": "serde",
        "downloads": 100,
        "url": "https://crates.io/crates/serde",
        "description": "A serialization framework",
    }
    result = _build(pkg)
    assert result["summary"] == "A serialization framework"


def test_url_passthrough():
    pkg = {
        "registry": "hex",
        "name": "phoenix",
        "downloads": 100,
        "url": "https://hex.pm/packages/phoenix",
    }
    result = _build(pkg)
    assert result["url"] == "https://hex.pm/packages/phoenix"
