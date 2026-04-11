"""Tests for source credibility tracking over time."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from digest.memory import FeedMemory
from digest.models import DigestResult, Item
from digest.source_tracker import SourceTracker, _accuracy


def _item(
    source: str = "hn",
    title: str = "Test",
    url: str = "https://example.com",
    engagement: int = 100,
) -> Item:
    return Item(
        source=source,
        title=title,
        url=url,
        timestamp=datetime.now(timezone.utc),
        engagement=engagement,
    )


def _result(items: list[Item], topic: str = "test") -> DigestResult:
    return DigestResult(topic=topic, days=30, items=items, narrative="n/a")


@pytest.fixture()
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "feed.db"


@pytest.fixture()
def mem(db_path: Path) -> FeedMemory:
    return FeedMemory(db_path=db_path)


# --- _accuracy ---


def test_accuracy_neutral_below_threshold():
    assert _accuracy(2, 1) == 1.0  # only 3 samples, need 5


def test_accuracy_perfect_hits():
    assert _accuracy(10, 0) == 1.5


def test_accuracy_all_misses():
    assert _accuracy(0, 10) == 0.5


def test_accuracy_even_split():
    assert _accuracy(5, 5) == 1.0


def test_accuracy_75_percent():
    result = _accuracy(15, 5)
    assert 1.2 < result < 1.3  # 0.5 + 0.75 = 1.25


# --- SourceTracker with no data ---


def test_tracker_nonexistent_db():
    tracker = SourceTracker(db_path=Path("/nonexistent/feed.db"))
    assert tracker.get_accuracy("hn", "test") == 1.0
    tracker.close()


def test_tracker_empty_scores(db_path: Path, mem: FeedMemory):
    mem.close()
    tracker = SourceTracker(db_path=db_path)
    assert tracker.get_accuracy("hn", "test") == 1.0
    assert tracker.get_all_scores("test") == {}
    tracker.close()


# --- update_scores ---


def test_update_needs_two_digests(db_path: Path, mem: FeedMemory):
    """No scores updated with only one digest."""
    mem.store(_result([_item(source="hn", url="https://a.com")]))
    mem.close()

    tracker = SourceTracker(db_path=db_path)
    result = tracker.update_scores("test")
    assert result == {}
    tracker.close()


def test_update_hit_when_url_persists(db_path: Path, mem: FeedMemory):
    """Item in both digests = hit for that source."""
    mem.store(_result([_item(source="hn", url="https://a.com")]))
    mem.store(_result([_item(source="hn", url="https://a.com")]))
    mem.close()

    tracker = SourceTracker(db_path=db_path)
    result = tracker.update_scores("test")
    assert result["hn"]["hits"] == 1
    assert result["hn"]["misses"] == 0
    tracker.close()


def test_update_miss_when_url_disappears(db_path: Path, mem: FeedMemory):
    """Item in first digest but not second = miss."""
    mem.store(_result([_item(source="hn", url="https://a.com")]))
    mem.store(_result([_item(source="hn", url="https://b.com")]))
    mem.close()

    tracker = SourceTracker(db_path=db_path)
    result = tracker.update_scores("test")
    assert result["hn"]["hits"] == 0
    assert result["hn"]["misses"] == 1
    tracker.close()


def test_update_mixed_sources(db_path: Path, mem: FeedMemory):
    """Different sources get separate tracking."""
    mem.store(_result([
        _item(source="hn", url="https://a.com"),
        _item(source="reddit", url="https://b.com"),
    ]))
    mem.store(_result([
        _item(source="hn", url="https://a.com"),  # hn persists
        _item(source="github", url="https://c.com"),  # reddit gone
    ]))
    mem.close()

    tracker = SourceTracker(db_path=db_path)
    result = tracker.update_scores("test")
    assert result["hn"]["hits"] == 1
    assert result["reddit"]["misses"] == 1
    assert "github" not in result  # wasn't in previous digest
    tracker.close()


def test_scores_accumulate(db_path: Path, mem: FeedMemory):
    """Running update_scores multiple times accumulates hits/misses."""
    mem.store(_result([_item(source="hn", url="https://a.com")]))
    mem.store(_result([_item(source="hn", url="https://a.com")]))
    mem.close()

    tracker = SourceTracker(db_path=db_path)
    tracker.update_scores("test")
    # Store a third digest and update again
    mem2 = FeedMemory(db_path=db_path)
    mem2.store(_result([_item(source="hn", url="https://a.com")]))
    mem2.close()
    tracker.update_scores("test")

    scores = tracker.get_all_scores("test")
    assert scores["hn"]["hits"] == 2
    assert scores["hn"]["samples"] == 2
    tracker.close()


def test_get_accuracy_with_enough_samples(db_path: Path, mem: FeedMemory):
    """Accuracy moves off neutral once there are 5+ samples."""
    # Store 6 pairs where hn always persists
    for i in range(6):
        mem.store(_result([_item(source="hn", url="https://a.com")]))
    mem.close()

    tracker = SourceTracker(db_path=db_path)
    # Update 5 times (each consecutive pair)
    for _ in range(5):
        tracker.update_scores("test")

    accuracy = tracker.get_accuracy("hn", "test")
    assert accuracy > 1.0  # all hits, should be above neutral
    tracker.close()


# --- Topics are isolated ---


def test_topics_isolated(db_path: Path, mem: FeedMemory):
    mem.store(_result([_item(source="hn", url="https://a.com")], topic="alpha"))
    mem.store(_result([_item(source="hn", url="https://a.com")], topic="alpha"))
    mem.store(_result([_item(source="hn", url="https://x.com")], topic="beta"))
    mem.store(_result([_item(source="hn", url="https://y.com")], topic="beta"))
    mem.close()

    tracker = SourceTracker(db_path=db_path)
    alpha = tracker.update_scores("alpha")
    beta = tracker.update_scores("beta")

    assert alpha["hn"]["hits"] == 1  # same URL persisted
    assert beta["hn"]["misses"] == 1  # different URLs
    tracker.close()
