"""Tests for credibility scoring."""

from __future__ import annotations

from datetime import datetime, timezone

from digest.credibility import (
    Tier,
    credibility_multiplier,
    source_tier,
)
from digest.models import Item


def _item(source: str, engagement: int = 100, **raw_kwargs: object) -> Item:
    return Item(
        source=source,
        title="test",
        url="https://example.com",
        timestamp=datetime.now(timezone.utc),
        engagement=engagement,
        raw=dict(raw_kwargs),
    )


# --- Tier classification ---


def test_polymarket_is_verified():
    assert source_tier("polymarket") == Tier.VERIFIED


def test_snapshot_is_verified():
    assert source_tier("snapshot") == Tier.VERIFIED


def test_blockscout_is_verified():
    assert source_tier("blockscout") == Tier.VERIFIED


def test_hn_is_deliberate():
    assert source_tier("hn") == Tier.DELIBERATE


def test_github_is_deliberate():
    assert source_tier("github") == Tier.DELIBERATE


def test_youtube_is_passive():
    assert source_tier("youtube") == Tier.PASSIVE


def test_packages_is_passive():
    assert source_tier("packages") == Tier.PASSIVE


def test_unknown_source_is_passive():
    assert source_tier("unknown_source") == Tier.PASSIVE


# --- Multiplier ordering ---


def test_verified_multiplier_higher_than_deliberate():
    verified = credibility_multiplier(_item("polymarket"))
    deliberate = credibility_multiplier(_item("hn"))
    assert verified > deliberate


def test_deliberate_multiplier_higher_than_passive():
    deliberate = credibility_multiplier(_item("hn"))
    passive = credibility_multiplier(_item("youtube"))
    assert deliberate > passive


# --- Per-item bonuses ---


def test_polymarket_high_liquidity_bonus():
    low_liq = credibility_multiplier(_item("polymarket", liquidity=5000))
    high_liq = credibility_multiplier(_item("polymarket", liquidity=200_000))
    assert high_liq > low_liq


def test_snapshot_high_votes_bonus():
    low = credibility_multiplier(_item("snapshot", votes=10))
    high = credibility_multiplier(_item("snapshot", votes=2000))
    assert high > low


def test_github_forks_bonus():
    no_forks = credibility_multiplier(_item("github", forks=0, open_issues=0))
    forked = credibility_multiplier(_item("github", forks=200, open_issues=100))
    assert forked > no_forks


def test_blockscout_high_value_bonus():
    small = credibility_multiplier(_item("blockscout", value_eth=0.01))
    large = credibility_multiplier(_item("blockscout", value_eth=500))
    assert large > small


def test_coingecko_top_rank_bonus():
    micro = credibility_multiplier(_item("coingecko", market_cap_rank=5000))
    top = credibility_multiplier(_item("coingecko", market_cap_rank=10))
    assert top > micro


def test_hn_high_engagement_bonus():
    low = credibility_multiplier(_item("hn", points=5, num_comments=1))
    high = credibility_multiplier(_item("hn", points=300, num_comments=100))
    assert high > low


def test_ethresearch_likes_bonus():
    low = credibility_multiplier(_item("ethresearch", like_count=0, posts_count=1))
    high = credibility_multiplier(_item("ethresearch", like_count=30, posts_count=15))
    assert high > low


# --- Integration with ranking ---


def test_verified_item_outranks_passive_with_same_engagement():
    from digest.ranking import score

    verified = _item("polymarket", engagement=100, liquidity=50_000)
    passive = _item("youtube", engagement=100)
    assert score(verified) > score(passive)
