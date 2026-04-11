"""Unit tests for YouTube adapter engagement and item building."""

from __future__ import annotations

from digest.adapters.youtube import YouTubeAdapter


def _build(entry: dict) -> dict | None:
    """Build an Item from a yt-dlp entry dict."""
    adapter = YouTubeAdapter()
    item = adapter._build_item(entry)
    if item is None:
        return None
    return {"engagement": item.engagement, "raw": item.raw, "url": item.url}


def test_engagement_normalizes_views():
    entry = {
        "id": "abc123",
        "title": "Test Video",
        "view_count": 100000,
        "like_count": 500,
        "comment_count": 50,
    }
    result = _build(entry)
    # 100000/100 + 500 + 50 = 1550
    assert result["engagement"] == 1550


def test_engagement_with_zero_views():
    entry = {
        "id": "abc123",
        "title": "New Upload",
        "view_count": 0,
        "like_count": 0,
        "comment_count": 0,
    }
    result = _build(entry)
    assert result["engagement"] == 0


def test_engagement_handles_missing_like_count():
    entry = {
        "id": "abc123",
        "title": "Video",
        "view_count": 5000,
    }
    result = _build(entry)
    # 5000/100 + 0 + 0 = 50
    assert result["engagement"] == 50


def test_returns_none_for_missing_id():
    entry = {"title": "No ID"}
    assert _build(entry) is None


def test_returns_none_for_missing_title():
    entry = {"id": "abc123"}
    assert _build(entry) is None


def test_url_format():
    entry = {"id": "dQw4w9WgXcQ", "title": "Video", "view_count": 1}
    result = _build(entry)
    assert result["url"] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def test_upload_date_parsing():
    adapter = YouTubeAdapter()
    entry = {
        "id": "abc",
        "title": "Video",
        "view_count": 1,
        "upload_date": "20260410",
    }
    item = adapter._build_item(entry)
    assert item.timestamp.year == 2026
    assert item.timestamp.month == 4
    assert item.timestamp.day == 10


def test_raw_preserves_channel_and_duration():
    entry = {
        "id": "abc",
        "title": "Video",
        "view_count": 100,
        "channel": "TestChannel",
        "duration": 360,
    }
    result = _build(entry)
    assert result["raw"]["channel"] == "TestChannel"
    assert result["raw"]["duration"] == 360
