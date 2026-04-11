"""Unit tests for Reddit adapter engagement and item building."""

from __future__ import annotations

from digest.adapters.reddit import RedditAdapter


def _build(post: dict) -> dict:
    """Build an Item from a Reddit post dict and return raw + engagement."""
    adapter = RedditAdapter()
    item = adapter._build_item(post)
    return {"engagement": item.engagement, "raw": item.raw, "url": item.url}


def test_engagement_combines_score_and_comments():
    post = {"score": 150, "num_comments": 30, "title": "test", "permalink": "/r/a/1"}
    result = _build(post)
    assert result["engagement"] == 180


def test_zero_engagement_for_empty_post():
    post = {"score": 0, "num_comments": 0, "title": "test", "permalink": "/r/a/2"}
    result = _build(post)
    assert result["engagement"] == 0


def test_url_includes_permalink():
    post = {
        "score": 1,
        "num_comments": 0,
        "title": "t",
        "permalink": "/r/test/comments/abc123/title/",
    }
    result = _build(post)
    assert result["url"] == "https://reddit.com/r/test/comments/abc123/title/"


def test_subreddit_in_raw():
    post = {"score": 1, "num_comments": 0, "title": "t", "permalink": "/r/x/1", "subreddit": "rust"}
    result = _build(post)
    assert result["raw"]["subreddit"] == "rust"


def test_days_to_time_filter():
    assert RedditAdapter._days_to_time_filter(1) == "day"
    assert RedditAdapter._days_to_time_filter(7) == "week"
    assert RedditAdapter._days_to_time_filter(14) == "month"
    assert RedditAdapter._days_to_time_filter(30) == "month"
    assert RedditAdapter._days_to_time_filter(90) == "year"
    assert RedditAdapter._days_to_time_filter(365) == "year"
    assert RedditAdapter._days_to_time_filter(400) == "all"
