"""Unit tests for feed memory (SQLite digest storage)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from digest.memory import FeedMemory
from digest.models import DigestResult, Item


@pytest.fixture()
def mem(tmp_path: Path) -> FeedMemory:
    return FeedMemory(db_path=tmp_path / "test_feed.db")


def _make_result(topic: str = "test", items: list[Item] | None = None) -> DigestResult:
    if items is None:
        items = [
            Item(
                source="hn",
                title="Test Item",
                url="https://example.com/1",
                timestamp=datetime.now(timezone.utc),
                engagement=100,
            ),
        ]
    return DigestResult(
        topic=topic,
        days=30,
        items=items,
        narrative="Test narrative",
    )


def test_store_returns_id(mem: FeedMemory) -> None:
    result = _make_result()
    digest_id = mem.store(result)
    assert digest_id >= 1


def test_digest_count(mem: FeedMemory) -> None:
    assert mem.digest_count("test") == 0
    mem.store(_make_result())
    assert mem.digest_count("test") == 1
    mem.store(_make_result())
    assert mem.digest_count("test") == 2


def test_previous_urls(mem: FeedMemory) -> None:
    result = _make_result()
    mem.store(result)
    urls = mem.previous_urls("test")
    assert "https://example.com/1" in urls


def test_previous_urls_empty_for_unknown_topic(mem: FeedMemory) -> None:
    urls = mem.previous_urls("nonexistent")
    assert len(urls) == 0


def test_url_appearances(mem: FeedMemory) -> None:
    result = _make_result()
    mem.store(result)
    mem.store(result)
    assert mem.url_appearances("test", "https://example.com/1") == 2


def test_url_appearances_zero_for_unknown(mem: FeedMemory) -> None:
    assert mem.url_appearances("test", "https://nope.com") == 0


def test_engagement_trend(mem: FeedMemory) -> None:
    items1 = [
        Item(
            source="hn",
            title="T",
            url="https://example.com/1",
            timestamp=datetime.now(timezone.utc),
            engagement=50,
        )
    ]
    items2 = [
        Item(
            source="hn",
            title="T",
            url="https://example.com/1",
            timestamp=datetime.now(timezone.utc),
            engagement=150,
        )
    ]
    mem.store(_make_result(items=items1))
    mem.store(_make_result(items=items2))

    trend = mem.engagement_trend("test", "https://example.com/1")
    assert trend == [50, 150]


def test_engagement_trend_empty_for_unknown(mem: FeedMemory) -> None:
    assert mem.engagement_trend("test", "https://nope.com") == []


def test_different_topics_isolated(mem: FeedMemory) -> None:
    mem.store(_make_result(topic="alpha"))
    mem.store(_make_result(topic="beta"))
    assert mem.digest_count("alpha") == 1
    assert mem.digest_count("beta") == 1
