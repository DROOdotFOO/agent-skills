"""Tests for deduplication against recall store."""

from pathlib import Path

from recall.models import Entry, EntryType
from recall.store import Store

from scribe.dedup import _token_overlap, deduplicate


def _make_entry(content: str, project: str = "test") -> Entry:
    return Entry(content=content, entry_type=EntryType.INSIGHT, project=project)


# -- token overlap -------------------------------------------------------------


def test_token_overlap_identical():
    assert _token_overlap("hello world", "hello world") == 1.0


def test_token_overlap_no_overlap():
    assert _token_overlap("hello world", "foo bar") == 0.0


def test_token_overlap_partial():
    overlap = _token_overlap("I prefer pathlib over os.path", "pathlib is better than os.path")
    assert 0.2 < overlap < 0.8


def test_token_overlap_empty():
    assert _token_overlap("", "hello") == 0.0
    assert _token_overlap("hello", "") == 0.0


def test_token_overlap_case_insensitive():
    assert _token_overlap("Hello World", "hello world") == 1.0


# -- deduplicate ---------------------------------------------------------------


def test_deduplicate_keeps_unique(tmp_path: Path):
    store = Store(db_path=tmp_path / "recall.db")

    # Add an existing entry
    store.add(
        Entry(
            content="use pydantic for data validation in Python",
            entry_type=EntryType.DECISION,
        )
    )

    # Candidate is different
    candidates = [_make_entry("prefer pathlib over os.path for file operations")]
    result = deduplicate(candidates, store)
    assert len(result) == 1
    store.close()


def test_deduplicate_removes_duplicate(tmp_path: Path):
    store = Store(db_path=tmp_path / "recall.db")

    store.add(
        Entry(
            content="I prefer pathlib over os.path always",
            entry_type=EntryType.DECISION,
        )
    )

    # Candidate is very similar
    candidates = [_make_entry("I prefer pathlib over os.path always")]
    result = deduplicate(candidates, store)
    assert len(result) == 0
    store.close()


def test_deduplicate_threshold(tmp_path: Path):
    store = Store(db_path=tmp_path / "recall.db")

    # Use exact same text so FTS5 finds it
    store.add(
        Entry(
            content="always use type hints in function signatures",
            entry_type=EntryType.DECISION,
        )
    )

    candidates = [_make_entry("always use type hints in function signatures")]

    # Low threshold = dedup catches it
    result_low = deduplicate(candidates, store, similarity_threshold=0.5)
    assert len(result_low) == 0

    # Threshold at 1.0 = nothing is "identical enough" unless exact
    # (Jaccard 1.0 requires identical token sets)
    result_high = deduplicate(candidates, store, similarity_threshold=1.0 + 0.01)
    assert len(result_high) == 1

    store.close()


def test_deduplicate_empty_store(tmp_path: Path):
    store = Store(db_path=tmp_path / "recall.db")
    candidates = [_make_entry("this is a new insight about testing")]
    result = deduplicate(candidates, store)
    assert len(result) == 1
    store.close()


def test_deduplicate_empty_candidates(tmp_path: Path):
    store = Store(db_path=tmp_path / "recall.db")
    result = deduplicate([], store)
    assert result == []
    store.close()


def test_deduplicate_multiple_candidates(tmp_path: Path):
    store = Store(db_path=tmp_path / "recall.db")

    store.add(
        Entry(
            content="avoid using mocks in integration tests",
            entry_type=EntryType.GOTCHA,
        )
    )

    candidates = [
        _make_entry("avoid using mocks in integration tests"),  # duplicate
        _make_entry("use pathlib for all file path operations"),  # unique
    ]
    result = deduplicate(candidates, store)
    assert len(result) == 1
    assert "pathlib" in result[0].content
    store.close()
