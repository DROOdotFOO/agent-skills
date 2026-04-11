"""Engagement-weighted ranking across platforms."""

from __future__ import annotations

import math
from datetime import datetime, timezone

from digest.models import Item

# Platform-specific weights to normalize engagement scales.
# HN upvotes are sparser than GitHub stars, so weight them higher.
PLATFORM_WEIGHTS: dict[str, float] = {
    "hn": 2.0,
    "github": 1.0,
    "reddit": 1.5,
    "youtube": 0.5,
    "x": 1.0,
    "ethresearch": 2.5,  # High-signal research forum, sparse engagement
    "snapshot": 1.5,  # Governance votes are deliberate signals
    "polymarket": 0.8,  # Volume is noisy, but odds are credibility signals
    "packages": 0.3,  # Downloads are massive numbers, scale down heavily
}


def score(item: Item, now: datetime | None = None) -> float:
    """Score an item by log-weighted engagement with a mild recency boost.

    Engagement is log-scaled so a 1000-point story doesn't drown a 50-point one.
    Recency decays linearly over 30 days.
    """
    now = now or datetime.now(timezone.utc)
    weight = PLATFORM_WEIGHTS.get(item.source, 1.0)
    engagement_score = math.log1p(max(item.engagement, 0)) * weight

    age_days = max((now - item.timestamp).total_seconds() / 86400, 0)
    recency = max(1.0 - age_days / 30, 0.1)

    return engagement_score * (0.7 + 0.3 * recency)


def rank(items: list[Item], limit: int | None = None) -> list[Item]:
    """Return items sorted by score descending, optionally truncated."""
    ranked = sorted(items, key=score, reverse=True)
    return ranked[:limit] if limit else ranked
