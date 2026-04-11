"""Tests for cross-platform deduplication."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from digest.dedup import _normalize_title, _normalize_url, _titles_similar, dedupe
from digest.models import Item


def _item(
    source: str = "hn",
    title: str = "Test",
    url: str = "https://example.com",
    engagement: int = 100,
    days_ago: int = 1,
) -> Item:
    return Item(
        source=source,
        title=title,
        url=url,
        timestamp=datetime.now(timezone.utc) - timedelta(days=days_ago),
        engagement=engagement,
    )


# --- URL normalization ---


def test_normalize_url_strips_protocol():
    assert _normalize_url("https://example.com/foo") == "example.com/foo"


def test_normalize_url_strips_www():
    assert _normalize_url("https://www.example.com/foo") == "example.com/foo"


def test_normalize_url_strips_trailing_slash():
    assert _normalize_url("https://example.com/foo/") == "example.com/foo"


def test_normalize_url_lowercases():
    assert _normalize_url("https://Example.COM/FOO") == "example.com/foo"


def test_normalize_url_http_and_https_match():
    assert _normalize_url("http://example.com/a") == _normalize_url("https://example.com/a")


# --- Title normalization ---


def test_normalize_title_lowercases():
    assert _normalize_title("Hello World") == "hello world"


def test_normalize_title_strips_punctuation():
    assert _normalize_title("Rust 2.0: What's New!") == "rust 2 0  what s new"


# --- Title similarity ---


def test_identical_titles_are_similar():
    assert _titles_similar("Rust 2.0 released", "Rust 2.0 released")


def test_titles_with_minor_diff_are_similar():
    assert _titles_similar("Rust 2.0 released", "Rust 2.0 released!")


def test_completely_different_titles_not_similar():
    assert not _titles_similar("Rust 2.0 released", "Python machine learning guide")


def test_custom_threshold():
    assert _titles_similar("abc def", "abc defg", threshold=0.7)
    assert not _titles_similar("abc def", "xyz uvw", threshold=0.7)


# --- Full dedupe ---


def test_dedupe_merges_same_url():
    items = [
        _item(source="hn", url="https://example.com/post", engagement=100),
        _item(source="reddit", url="https://example.com/post/", engagement=50),
    ]
    result = dedupe(items)
    assert len(result) == 1
    assert result[0].engagement == 150


def test_dedupe_merges_similar_titles():
    items = [
        _item(source="hn", title="Noir ZK proofs are fast", url="https://a.com", engagement=80),
        _item(
            source="reddit", title="Noir ZK proofs are fast!", url="https://b.com", engagement=40
        ),
    ]
    result = dedupe(items)
    assert len(result) == 1


def test_dedupe_keeps_distinct_items():
    items = [
        _item(title="Rust async", url="https://a.com"),
        _item(title="Python typing", url="https://b.com"),
    ]
    result = dedupe(items)
    assert len(result) == 2


def test_dedupe_keeps_higher_scorer():
    items = [
        _item(source="hn", url="https://a.com", engagement=200),
        _item(source="packages", url="https://a.com", engagement=50),
    ]
    result = dedupe(items)
    assert len(result) == 1
    assert result[0].source == "hn"


def test_dedupe_empty_list():
    assert dedupe([]) == []


def test_dedupe_single_item():
    items = [_item()]
    result = dedupe(items)
    assert len(result) == 1
