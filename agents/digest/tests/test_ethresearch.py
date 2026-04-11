"""Unit tests for ethresear.ch engagement calculation and item building.

Verifies that the composite engagement metric weights likes heavily
(they are sparse on ethresear.ch) and rewards discussion depth.
"""

from __future__ import annotations

from digest.adapters.ethresearch import EthResearchAdapter


def _engagement_from_topic(topic: dict) -> int:
    """Replicate the engagement formula from EthResearchAdapter."""
    return EthResearchAdapter._engagement(topic)


def test_views_contribute_linearly():
    topic = {"views": 500, "like_count": 0, "posts_count": 0}
    assert _engagement_from_topic(topic) == 500


def test_likes_weighted_5x():
    topic = {"views": 0, "like_count": 10, "posts_count": 0}
    assert _engagement_from_topic(topic) == 50


def test_posts_weighted_3x():
    topic = {"views": 0, "like_count": 0, "posts_count": 7}
    assert _engagement_from_topic(topic) == 21


def test_combined_engagement():
    topic = {"views": 200, "like_count": 5, "posts_count": 10}
    # 200 + 25 + 30 = 255
    assert _engagement_from_topic(topic) == 255


def test_high_likes_beats_high_views():
    """A well-liked post should score higher than a merely viewed one."""
    liked = {"views": 100, "like_count": 20, "posts_count": 0}
    viewed = {"views": 180, "like_count": 0, "posts_count": 0}
    # liked: 100 + 100 + 0 = 200; viewed: 180
    assert _engagement_from_topic(liked) > _engagement_from_topic(viewed)


def test_zero_engagement_for_empty_topic():
    empty = {"views": 0, "like_count": 0, "posts_count": 0}
    assert _engagement_from_topic(empty) == 0


def test_build_item_url_format():
    adapter = EthResearchAdapter()
    topic = {
        "id": 42,
        "title": "EIP-4844 analysis",
        "slug": "eip-4844-analysis",
        "created_at": "2026-01-15T10:30:00Z",
        "views": 300,
        "like_count": 8,
        "posts_count": 5,
        "tags": ["eip-4844", "proto-danksharding"],
    }
    item = adapter._build_item(topic)
    assert item.source == "ethresearch"
    assert item.url == "https://ethresear.ch/t/eip-4844-analysis/42"
    assert item.title == "EIP-4844 analysis"
    assert item.engagement == 300 + 8 * 5 + 5 * 3  # 355
    assert item.raw["tags"] == ["eip-4844", "proto-danksharding"]
    assert item.raw["topic_id"] == 42
