"""Tests for structured output views."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from digest.models import DigestResult, Item
from digest.views import (
    all_views,
    controversy_view,
    source_breakdown_view,
    tag_trends_view,
    timeline_view,
)


def _item(
    source: str = "hn",
    title: str = "Test Item",
    url: str = "https://example.com",
    engagement: int = 100,
    days_ago: int = 1,
    **raw_kwargs: object,
) -> Item:
    return Item(
        source=source,
        title=title,
        url=url,
        timestamp=datetime.now(timezone.utc) - timedelta(days=days_ago),
        engagement=engagement,
        raw=dict(raw_kwargs),
    )


def _result(items: list[Item], topic: str = "test") -> DigestResult:
    return DigestResult(topic=topic, days=30, items=items, narrative="n/a")


# --- Timeline ---


def test_timeline_groups_by_recency():
    items = [
        _item(title="Today", days_ago=0),
        _item(title="This week", days_ago=3),
        _item(title="Old", days_ago=15),
    ]
    text = timeline_view(_result(items))
    assert "Last 24 hours" in text
    assert "This week" in text
    assert "Older" in text


def test_timeline_skips_empty_buckets():
    items = [_item(title="Old", days_ago=15)]
    text = timeline_view(_result(items))
    assert "Last 24 hours" not in text
    assert "Older" in text


def test_timeline_empty():
    text = timeline_view(_result([]))
    assert "No items" in text


# --- Controversy ---


def test_controversy_detects_multi_source():
    items = [
        _item(source="hn", title="Rust async debate"),
        _item(source="reddit", title="Rust async debate"),
    ]
    text = controversy_view(_result(items))
    assert "2 sources" in text


def test_controversy_detects_gainer_loser_conflict():
    items = [
        _item(source="coingecko", title="crypto token surging", type="top_gainers"),
        _item(source="coingecko", title="crypto token crashing", type="top_losers"),
    ]
    text = controversy_view(_result(items))
    assert "[!]" in text


def test_controversy_no_conflict():
    items = [_item(title="Solo item")]
    text = controversy_view(_result(items))
    assert "consistent" in text.lower() or "No controversial" in text


# --- Tags ---


def test_tag_trends_extracts_from_titles():
    items = [
        _item(title="Rust 2.0 async improvements"),
        _item(title="Rust compiler speedup"),
    ]
    text = tag_trends_view(_result(items))
    assert "rust" in text.lower()
    assert "| Tag |" in text


def test_tag_trends_empty():
    text = tag_trends_view(_result([]))
    assert "Tag" in text  # header still present


# --- Source breakdown ---


def test_source_breakdown_shows_tiers():
    items = [
        _item(source="polymarket", title="PM item"),
        _item(source="hn", title="HN item"),
        _item(source="youtube", title="YT item"),
    ]
    text = source_breakdown_view(_result(items))
    assert "verified" in text
    assert "deliberate" in text
    assert "passive" in text


def test_source_breakdown_table():
    items = [_item(source="hn"), _item(source="github")]
    text = source_breakdown_view(_result(items))
    assert "| Source |" in text
    assert "| hn |" in text
    assert "| github |" in text


# --- All views ---


def test_all_views_combines():
    items = [
        _item(source="hn", title="Test A", days_ago=0),
        _item(source="github", title="Test B", days_ago=3),
    ]
    text = all_views(_result(items))
    assert "Source Breakdown" in text
    assert "Timeline" in text
    assert "Tag Analysis" in text
    assert "Controversy Map" in text
