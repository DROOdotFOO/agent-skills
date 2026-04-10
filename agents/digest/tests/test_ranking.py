"""Tests for ranking and dedup logic (no network, no API calls)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from digest.dedup import dedupe
from digest.models import Item
from digest.ranking import rank, score


def make_item(
    source: str,
    title: str,
    url: str,
    engagement: int,
    days_ago: int = 1,
) -> Item:
    return Item(
        source=source,
        title=title,
        url=url,
        timestamp=datetime.now(timezone.utc) - timedelta(days=days_ago),
        engagement=engagement,
    )


def test_higher_engagement_scores_higher():
    low = make_item("hn", "A", "https://a.com", 10)
    high = make_item("hn", "B", "https://b.com", 1000)
    assert score(high) > score(low)


def test_recent_items_score_higher_than_old():
    recent = make_item("hn", "A", "https://a.com", 100, days_ago=1)
    old = make_item("hn", "B", "https://b.com", 100, days_ago=29)
    assert score(recent) > score(old)


def test_rank_sorts_descending():
    items = [
        make_item("hn", "low", "https://a.com", 5),
        make_item("hn", "high", "https://b.com", 500),
        make_item("hn", "mid", "https://c.com", 50),
    ]
    ranked = rank(items)
    assert [i.title for i in ranked] == ["high", "mid", "low"]


def test_dedupe_merges_same_url_across_platforms():
    items = [
        make_item("hn", "Story about X", "https://example.com/post", 100),
        make_item("github", "Story about X", "https://example.com/post/", 50),
    ]
    result = dedupe(items)
    assert len(result) == 1
    # Higher-scoring item wins, engagement merged
    assert result[0].engagement == 150


def test_dedupe_keeps_distinct_items():
    items = [
        make_item("hn", "Completely unrelated thing", "https://a.com", 100),
        make_item("github", "Some other project", "https://b.com", 50),
    ]
    result = dedupe(items)
    assert len(result) == 2


def test_dedupe_merges_similar_titles_across_urls():
    items = [
        make_item("hn", "Rust 2.0 released with async improvements", "https://rust-lang.org/post1", 200),
        make_item("reddit", "Rust 2.0 released with async improvements!", "https://reddit.com/r/rust/post2", 80),
    ]
    result = dedupe(items)
    assert len(result) == 1
