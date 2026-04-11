"""Unit tests for Polymarket adapter engagement and item building."""

from __future__ import annotations

from digest.adapters.polymarket import PolymarketAdapter


def _build(market: dict) -> dict | None:
    """Build an Item from a Gamma API market dict."""
    adapter = PolymarketAdapter()
    item = adapter._build_item(market)
    return {"engagement": item.engagement, "raw": item.raw, "url": item.url}


def test_engagement_is_volume():
    market = {
        "question": "Will BTC hit 100k?",
        "volume": "1500000.50",
        "liquidity": "250000",
        "slug": "btc-100k",
    }
    result = _build(market)
    assert result["engagement"] == 1500000


def test_engagement_zero_for_missing_volume():
    market = {
        "question": "Will ETH flip BTC?",
        "slug": "eth-flip",
    }
    result = _build(market)
    assert result["engagement"] == 0


def test_engagement_handles_numeric_volume():
    market = {
        "question": "Some market",
        "volume": 42000,
        "slug": "some-market",
    }
    result = _build(market)
    assert result["engagement"] == 42000


def test_engagement_handles_invalid_volume():
    market = {
        "question": "Some market",
        "volume": "not-a-number",
        "slug": "some-market",
    }
    result = _build(market)
    assert result["engagement"] == 0


def test_url_from_slug():
    market = {
        "question": "Test market",
        "slug": "test-market",
        "volume": "100",
    }
    result = _build(market)
    assert result["url"] == "https://polymarket.com/event/test-market"


def test_url_fallback_when_no_slug():
    market = {
        "question": "Test market",
        "volume": "100",
    }
    result = _build(market)
    assert result["url"] == "https://polymarket.com"


def test_raw_preserves_market_data():
    market = {
        "question": "Will it rain?",
        "volume": "5000",
        "liquidity": "1200",
        "outcomes": "Yes,No",
        "outcomePrices": "0.65,0.35",
        "endDate": "2026-12-31T00:00:00Z",
        "active": True,
        "closed": False,
        "slug": "rain",
    }
    result = _build(market)
    assert result["raw"]["volume"] == 5000
    assert result["raw"]["liquidity"] == 1200
    assert result["raw"]["outcomes"] == "Yes,No"
    assert result["raw"]["outcome_prices"] == "0.65,0.35"
    assert result["raw"]["end_date"] == "2026-12-31T00:00:00Z"
    assert result["raw"]["active"] is True
    assert result["raw"]["closed"] is False


def test_end_date_parsing():
    adapter = PolymarketAdapter()
    market = {
        "question": "Test",
        "volume": "100",
        "endDate": "2026-06-15T12:00:00Z",
        "slug": "test",
    }
    item = adapter._build_item(market)
    assert item.timestamp.year == 2026
    assert item.timestamp.month == 6
    assert item.timestamp.day == 15


def test_end_date_fallback_when_missing():
    adapter = PolymarketAdapter()
    market = {
        "question": "Test",
        "volume": "100",
        "slug": "test",
    }
    item = adapter._build_item(market)
    # Falls back to now -- just verify it parsed without error
    assert item.timestamp is not None
