"""Tests for recall data models."""

from __future__ import annotations

from recall.models import Entry, EntryType, SearchResult


class TestEntry:
    def test_default_type_is_insight(self):
        e = Entry(content="test")
        assert e.entry_type == EntryType.INSIGHT

    def test_tags_str_joins(self):
        e = Entry(content="test", tags=["a", "b", "c"])
        assert e.tags_str == "a,b,c"

    def test_tags_str_empty(self):
        e = Entry(content="test")
        assert e.tags_str == ""

    def test_from_row(self):
        row = {
            "id": 1,
            "content": "test content",
            "entry_type": "decision",
            "project": "myproj",
            "tags": "python,sqlite",
            "source": "manual",
            "created_at": "2026-04-11T00:00:00",
            "updated_at": "2026-04-11T00:00:00",
            "accessed_at": None,
            "access_count": 0,
        }
        e = Entry.from_row(row)
        assert e.id == 1
        assert e.entry_type == EntryType.DECISION
        assert e.tags == ["python", "sqlite"]
        assert e.project == "myproj"

    def test_from_row_empty_tags(self):
        row = {
            "id": 2,
            "content": "test",
            "entry_type": "insight",
            "project": None,
            "tags": "",
            "source": None,
            "created_at": None,
            "updated_at": None,
            "accessed_at": None,
            "access_count": 0,
        }
        e = Entry.from_row(row)
        assert e.tags == []


class TestEntryType:
    def test_all_types_exist(self):
        assert len(EntryType) == 5
        assert EntryType.DECISION.value == "decision"
        assert EntryType.PATTERN.value == "pattern"
        assert EntryType.GOTCHA.value == "gotcha"
        assert EntryType.LINK.value == "link"
        assert EntryType.INSIGHT.value == "insight"


class TestSearchResult:
    def test_wraps_entry(self):
        e = Entry(content="test", id=1)
        sr = SearchResult(entry=e, rank=-1.5, snippet="...test...")
        assert sr.entry.content == "test"
        assert sr.rank == -1.5
        assert sr.snippet == "...test..."
