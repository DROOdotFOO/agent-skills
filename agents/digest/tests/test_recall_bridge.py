"""Tests for the digest <-> recall bridge."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from digest.models import DigestResult, Item
from digest.recall_bridge import (
    fetch_from_recall,
    format_recall_context,
    recall_available,
    store_to_recall,
)


def _item(title: str = "Test", url: str = "https://example.com", engagement: int = 100) -> Item:
    return Item(
        source="hn",
        title=title,
        url=url,
        timestamp=datetime.now(timezone.utc),
        engagement=engagement,
    )


def _result(topic: str = "noir", items: list[Item] | None = None) -> DigestResult:
    if items is None:
        items = [_item()]
    return DigestResult(topic=topic, days=30, items=items, narrative="n/a")


# --- recall_available ---


def test_recall_available_false_for_nonexistent():
    assert not recall_available(Path("/nonexistent/recall.db"))


def test_recall_available_true_for_existing(tmp_path: Path):
    db = tmp_path / "recall.db"
    db.touch()
    assert recall_available(db)


# --- format_recall_context ---


def test_format_empty():
    assert format_recall_context([]) == ""


def test_format_with_entries():
    entries = [
        {"content": "We decided to use WAL mode", "type": "decision", "tags": "sqlite", "project": "recall"},
        {"content": "Noir circuits need fewer constraints", "type": "insight", "tags": "noir,zk", "project": "noir"},
    ]
    text = format_recall_context(entries)
    assert "Historical context" in text
    assert "decision" in text
    assert "WAL mode" in text
    assert "insight" in text


# --- store_to_recall (requires recall package) ---


@pytest.fixture()
def recall_store(tmp_path: Path):
    """Create a temporary recall store."""
    try:
        from recall.store import Store

        store = Store(db_path=tmp_path / "recall.db")
        # Trigger schema creation
        _ = store.conn
        store.close()
        return tmp_path / "recall.db"
    except ImportError:
        pytest.skip("recall package not installed")


def test_store_to_recall_adds_entries(recall_store: Path):
    items = [
        _item("Noir 1.0 released", "https://noir.org/1.0", 500),
        _item("ZK benchmarks", "https://zk.dev/bench", 300),
        _item("Aztec update", "https://aztec.network/up", 200),
    ]
    result = _result("noir", items)
    added = store_to_recall(result, top_n=3, db_path=recall_store)
    assert added == 3


def test_store_to_recall_skips_duplicates(recall_store: Path):
    result = _result("noir", [_item("Same item", "https://same.com")])
    first = store_to_recall(result, top_n=1, db_path=recall_store)
    second = store_to_recall(result, top_n=1, db_path=recall_store)
    assert first == 1
    assert second == 0


def test_store_to_recall_respects_top_n(recall_store: Path):
    items = [_item(f"Item {i}", f"https://example.com/{i}") for i in range(10)]
    result = _result("test", items)
    added = store_to_recall(result, top_n=3, db_path=recall_store)
    assert added == 3


# --- fetch_from_recall ---


def test_fetch_from_recall_returns_entries(recall_store: Path):
    # First store something
    result = _result("noir", [_item("Noir ZK proofs", "https://noir.org")])
    store_to_recall(result, db_path=recall_store)

    # Then fetch
    entries = fetch_from_recall("noir", db_path=recall_store)
    assert len(entries) >= 1
    assert any("noir" in e["content"].lower() for e in entries)


def test_fetch_from_recall_empty_for_unknown_topic(recall_store: Path):
    entries = fetch_from_recall("nonexistent_topic_xyz", db_path=recall_store)
    assert entries == []


def test_fetch_returns_empty_when_no_store():
    entries = fetch_from_recall("anything", db_path=Path("/nonexistent/recall.db"))
    assert entries == []
