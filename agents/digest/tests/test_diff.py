"""Unit tests for differential digest classification."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from digest.diff import Trend, classify_items, format_differential
from digest.memory import FeedMemory
from digest.models import DigestResult, Item


@pytest.fixture()
def mem(tmp_path: Path) -> FeedMemory:
    return FeedMemory(db_path=tmp_path / "test_feed.db")


def _item(url: str, engagement: int = 100) -> Item:
    return Item(
        source="hn",
        title=f"Item {url}",
        url=url,
        timestamp=datetime.now(timezone.utc),
        engagement=engagement,
    )


def _result(items: list[Item], topic: str = "test") -> DigestResult:
    return DigestResult(topic=topic, days=30, items=items, narrative="n/a")


def test_all_new_when_no_history(mem: FeedMemory) -> None:
    result = _result([_item("https://a.com"), _item("https://b.com")])
    classified = classify_items(result, mem)
    assert len(classified[Trend.NEW]) == 2
    assert len(classified[Trend.ONGOING]) == 0


def test_ongoing_when_seen_before(mem: FeedMemory) -> None:
    item = _item("https://a.com", engagement=100)
    mem.store(_result([item]))
    mem.store(_result([item]))

    new_result = _result([_item("https://a.com", engagement=100)])
    classified = classify_items(new_result, mem)
    assert len(classified[Trend.ONGOING]) == 1


def test_accelerating_when_engagement_jumps(mem: FeedMemory) -> None:
    mem.store(_result([_item("https://a.com", engagement=50)]))
    mem.store(_result([_item("https://a.com", engagement=60)]))

    new_result = _result([_item("https://a.com", engagement=200)])
    classified = classify_items(new_result, mem)
    assert len(classified[Trend.ACCELERATING]) == 1


def test_declining_when_engagement_drops(mem: FeedMemory) -> None:
    mem.store(_result([_item("https://a.com", engagement=200)]))
    mem.store(_result([_item("https://a.com", engagement=180)]))

    new_result = _result([_item("https://a.com", engagement=50)])
    classified = classify_items(new_result, mem)
    assert len(classified[Trend.DECLINING]) == 1


def test_format_differential_new_items(mem: FeedMemory) -> None:
    result = _result([_item("https://a.com")])
    classified = classify_items(result, mem)
    text = format_differential(classified)
    assert "New since last digest" in text
    assert "https://a.com" in text


def test_format_differential_empty() -> None:
    classified = {
        Trend.NEW: [],
        Trend.ACCELERATING: [],
        Trend.ONGOING: [],
        Trend.DECLINING: [],
    }
    text = format_differential(classified)
    assert text == "No items to classify."
