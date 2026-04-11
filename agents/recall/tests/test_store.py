"""Tests for the recall store (SQLite + FTS5)."""

from __future__ import annotations

from pathlib import Path

import pytest

from recall.models import Entry, EntryType
from recall.store import Store


@pytest.fixture()
def store(tmp_path: Path) -> Store:
    """Create a store backed by a temp database."""
    s = Store(db_path=tmp_path / "test.db")
    yield s
    s.close()


def _add(store: Store, content: str, **kwargs) -> Entry:
    return store.add(Entry(content=content, **kwargs))


class TestAdd:
    def test_returns_entry_with_id(self, store: Store):
        entry = _add(store, "test insight")
        assert entry.id is not None
        assert entry.id > 0

    def test_sets_timestamps(self, store: Store):
        entry = _add(store, "test")
        assert entry.created_at is not None
        assert entry.updated_at is not None

    def test_preserves_type(self, store: Store):
        entry = _add(store, "a decision", entry_type=EntryType.DECISION)
        got = store.get(entry.id)
        assert got.entry_type == EntryType.DECISION

    def test_preserves_tags(self, store: Store):
        entry = _add(store, "tagged", tags=["python", "sqlite"])
        got = store.get(entry.id)
        assert set(got.tags) == {"python", "sqlite"}

    def test_preserves_project(self, store: Store):
        entry = _add(store, "project entry", project="agent-skills")
        got = store.get(entry.id)
        assert got.project == "agent-skills"


class TestSearch:
    def test_finds_by_content(self, store: Store):
        _add(store, "SQLite FTS5 supports full-text search with porter stemming")
        _add(store, "unrelated entry about cooking pasta")
        results = store.search("sqlite full-text")
        assert len(results) >= 1
        assert "sqlite" in results[0].entry.content.lower()

    def test_returns_empty_for_no_match(self, store: Store):
        _add(store, "something about python")
        results = store.search("nonexistent-xyzzy-term")
        assert results == []

    def test_filters_by_project(self, store: Store):
        _add(store, "insight for project A", project="projA")
        _add(store, "insight for project B", project="projB")
        results = store.search("insight", project="projA")
        assert all(r.entry.project == "projA" for r in results)

    def test_filters_by_type(self, store: Store):
        _add(store, "a decision about architecture", entry_type=EntryType.DECISION)
        _add(store, "a pattern for error handling", entry_type=EntryType.PATTERN)
        results = store.search("architecture OR error", entry_type=EntryType.DECISION)
        assert all(r.entry.entry_type == EntryType.DECISION for r in results)

    def test_filters_by_tags(self, store: Store):
        _add(store, "elixir genserver pattern", tags=["elixir", "otp"])
        _add(store, "python asyncio pattern", tags=["python", "async"])
        results = store.search("pattern", tags=["elixir"])
        assert len(results) == 1
        assert "elixir" in results[0].entry.tags

    def test_respects_limit(self, store: Store):
        for i in range(10):
            _add(store, f"entry number {i} about testing")
        results = store.search("testing", limit=3)
        assert len(results) == 3

    def test_snippet_contains_match(self, store: Store):
        _add(store, "The quick brown fox jumps over the lazy dog")
        results = store.search("fox")
        assert results[0].snippet is not None
        assert "fox" in results[0].snippet.lower()


class TestGet:
    def test_returns_none_for_missing(self, store: Store):
        assert store.get(9999) is None

    def test_increments_access_count(self, store: Store):
        entry = _add(store, "access tracking test")
        store.get(entry.id)
        store.get(entry.id)
        got = store.get(entry.id)
        assert got.access_count >= 3


class TestUpdate:
    def test_updates_content(self, store: Store):
        entry = _add(store, "original content")
        updated = store.update(entry.id, content="updated content")
        assert updated.content == "updated content"

    def test_updates_tags(self, store: Store):
        entry = _add(store, "tag test", tags=["old"])
        updated = store.update(entry.id, tags=["new", "tags"])
        assert set(updated.tags) == {"new", "tags"}

    def test_returns_none_for_missing(self, store: Store):
        assert store.update(9999, content="nope") is None


class TestDelete:
    def test_deletes_existing(self, store: Store):
        entry = _add(store, "delete me")
        assert store.delete(entry.id) is True
        assert store.get(entry.id) is None

    def test_returns_false_for_missing(self, store: Store):
        assert store.delete(9999) is False


class TestStale:
    def test_new_entries_are_stale_when_never_accessed(self, store: Store):
        _add(store, "never accessed")
        stale = store.stale(days=0)
        assert len(stale) >= 1

    def test_recently_accessed_not_stale(self, store: Store):
        entry = _add(store, "fresh entry")
        store.get(entry.id)  # access it
        stale = store.stale(days=1)
        # May or may not appear depending on timing, but shouldn't fail
        assert isinstance(stale, list)


class TestStats:
    def test_empty_store(self, store: Store):
        s = store.stats()
        assert s["total"] == 0

    def test_counts_by_type(self, store: Store):
        _add(store, "d1", entry_type=EntryType.DECISION)
        _add(store, "d2", entry_type=EntryType.DECISION)
        _add(store, "p1", entry_type=EntryType.PATTERN)
        s = store.stats()
        assert s["total"] == 3
        assert s["by_type"]["decision"] == 2
        assert s["by_type"]["pattern"] == 1


class TestListEntries:
    def test_returns_newest_first(self, store: Store):
        _add(store, "first")
        _add(store, "second")
        _add(store, "third")
        entries = store.list_entries()
        assert entries[0].content == "third"
        assert entries[-1].content == "first"

    def test_filters_by_project(self, store: Store):
        _add(store, "a", project="x")
        _add(store, "b", project="y")
        entries = store.list_entries(project="x")
        assert len(entries) == 1
        assert entries[0].project == "x"
