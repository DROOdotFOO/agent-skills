"""Structured output views for digest results.

Each view takes a DigestResult and returns a markdown string presenting
the same data from a different angle: timeline, controversy, tags, sources.
"""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from digest.credibility import Tier, source_tier
from digest.models import DigestResult, Item


def timeline_view(result: DigestResult) -> str:
    """Group items by time bucket: today, this week, older."""
    now = datetime.now(timezone.utc)
    today = now - timedelta(days=1)
    this_week = now - timedelta(days=7)

    buckets: dict[str, list[Item]] = {
        "Last 24 hours": [],
        "This week": [],
        "Older": [],
    }

    for item in result.items:
        if item.timestamp >= today:
            buckets["Last 24 hours"].append(item)
        elif item.timestamp >= this_week:
            buckets["This week"].append(item)
        else:
            buckets["Older"].append(item)

    lines = [f"# Timeline: {result.topic}\n"]
    for label, items in buckets.items():
        if not items:
            continue
        lines.append(f"## {label} ({len(items)} items)\n")
        for item in items:
            date_str = item.timestamp.strftime("%b %d")
            lines.append(f"- [{item.source}] {date_str} -- [{item.title}]({item.url})")
        lines.append("")

    return "\n".join(lines) if len(lines) > 1 else "No items to display."


def controversy_view(result: DigestResult) -> str:
    """Cluster items by extracted topics and flag conflicting signals.

    A topic is "controversial" when it appears across multiple sources
    with divergent credibility tiers or when coingecko shows both
    gainers and losers for related tokens.
    """
    clusters = _cluster_by_keywords(result.items)

    lines = [f"# Controversy Map: {result.topic}\n"]
    found_controversy = False

    for topic, items in sorted(clusters.items(), key=lambda x: -len(x[1])):
        if len(items) < 2:
            continue

        tiers = {source_tier(i.source) for i in items}
        sources = {i.source for i in items}
        has_conflicting_signals = _has_conflict(items)

        if len(tiers) > 1 or len(sources) > 1 or has_conflicting_signals:
            found_controversy = True
            marker = " [!]" if has_conflicting_signals else ""
            lines.append(f"## {topic}{marker} ({len(items)} items, {len(sources)} sources)\n")

            for item in items:
                tier_label = source_tier(item.source).value
                lines.append(f"- [{item.source}/{tier_label}] [{item.title}]({item.url})")
            lines.append("")

    if not found_controversy:
        lines.append("No controversial topics detected -- signals are consistent.\n")

    return "\n".join(lines)


def tag_trends_view(result: DigestResult) -> str:
    """Extract tags/topics from items and show frequency + source diversity.

    Tags are extracted from titles via simple keyword extraction.
    """
    tag_items: dict[str, list[Item]] = defaultdict(list)

    for item in result.items:
        tags = _extract_tags(item)
        for tag in tags:
            tag_items[tag].append(item)

    # Sort by count descending, then by source diversity
    sorted_tags = sorted(
        tag_items.items(),
        key=lambda x: (len(x[1]), len({i.source for i in x[1]})),
        reverse=True,
    )

    lines = [f"# Tag Analysis: {result.topic}\n"]
    lines.append("| Tag | Count | Sources | Top source |")
    lines.append("|-----|-------|---------|------------|")

    for tag, items in sorted_tags[:30]:
        sources = {i.source for i in items}
        top_source = max(sources, key=lambda s: sum(1 for i in items if i.source == s))
        lines.append(f"| {tag} | {len(items)} | {', '.join(sorted(sources))} | {top_source} |")

    lines.append("")
    return "\n".join(lines)


def source_breakdown_view(result: DigestResult) -> str:
    """Cross-platform signal comparison: items per source, tier distribution."""
    by_source: dict[str, list[Item]] = defaultdict(list)
    for item in result.items:
        by_source[item.source].append(item)

    by_tier: dict[Tier, int] = defaultdict(int)
    for item in result.items:
        by_tier[source_tier(item.source)] += 1

    lines = [f"# Source Breakdown: {result.topic}\n"]

    # Tier summary
    lines.append("## Signal quality\n")
    total = len(result.items)
    for tier in (Tier.VERIFIED, Tier.DELIBERATE, Tier.PASSIVE):
        count = by_tier.get(tier, 0)
        pct = (count / total * 100) if total else 0
        bar = "#" * int(pct / 5)
        lines.append(f"- **{tier.value}**: {count} items ({pct:.0f}%) {bar}")
    lines.append("")

    # Per-source table
    lines.append("## Per source\n")
    lines.append("| Source | Items | Avg engagement | Tier |")
    lines.append("|--------|-------|----------------|------|")

    for source in sorted(by_source, key=lambda s: -len(by_source[s])):
        items = by_source[source]
        avg_eng = sum(i.engagement for i in items) / len(items) if items else 0
        tier = source_tier(source).value
        lines.append(f"| {source} | {len(items)} | {avg_eng:.0f} | {tier} |")

    lines.append("")
    return "\n".join(lines)


def all_views(result: DigestResult) -> str:
    """Combine all structured views into one output."""
    sections = [
        source_breakdown_view(result),
        timeline_view(result),
        tag_trends_view(result),
        controversy_view(result),
    ]
    return "\n---\n\n".join(sections)


# --- helpers ---


def _extract_tags(item: Item) -> list[str]:
    """Extract meaningful tags from an item's title and raw data."""
    tags: list[str] = []

    # From raw data
    raw_tags = item.raw.get("tags", [])
    if isinstance(raw_tags, list):
        tags.extend(str(t).lower() for t in raw_tags)

    # From title: extract capitalized words and known patterns
    title = item.title
    # Remove bracket prefixes like [Trending], [Transfer], etc.
    title_clean = re.sub(r"\[.*?\]\s*", "", title)

    words = title_clean.split()
    for word in words:
        w = re.sub(r"[^a-zA-Z0-9-]", "", word).lower()
        if len(w) >= 3 and w not in _STOP_WORDS:
            tags.append(w)

    return list(dict.fromkeys(tags))[:8]  # dedupe, limit per item


def _cluster_by_keywords(items: list[Item]) -> dict[str, list[Item]]:
    """Cluster items that share significant keywords."""
    clusters: dict[str, list[Item]] = defaultdict(list)

    for item in items:
        tags = _extract_tags(item)
        # Use the most significant tag as the cluster key
        for tag in tags[:3]:
            clusters[tag].append(item)

    # Only return clusters with 2+ items
    return {k: v for k, v in clusters.items() if len(v) >= 2}


def _has_conflict(items: list[Item]) -> bool:
    """Check if items show conflicting signals (e.g. gainers vs losers)."""
    types = {item.raw.get("type", "") for item in items}

    # CoinGecko: gainer vs loser on related tokens
    if "top_gainers" in types and "top_losers" in types:
        return True

    # Polymarket: look for high-confidence opposing outcomes
    for item in items:
        prices = item.raw.get("outcome_prices", "")
        if isinstance(prices, str) and prices:
            try:
                import json

                parsed = json.loads(prices)
                if len(parsed) >= 2:
                    vals = [float(p) for p in parsed]
                    # Both outcomes near 50/50 means genuine uncertainty
                    if all(0.35 < v < 0.65 for v in vals):
                        return True
            except (json.JSONDecodeError, ValueError):
                pass

    return False


_STOP_WORDS = frozenset(
    {
        "the",
        "and",
        "for",
        "with",
        "from",
        "that",
        "this",
        "are",
        "was",
        "has",
        "have",
        "not",
        "but",
        "its",
        "you",
        "all",
        "can",
        "been",
        "will",
        "new",
        "how",
        "what",
        "when",
        "who",
        "why",
        "about",
        "into",
        "more",
        "some",
        "than",
        "them",
        "then",
        "just",
        "also",
        "over",
        "after",
        "before",
        "between",
        "each",
        "few",
        "most",
        "other",
        "such",
        "very",
        "own",
        "same",
        "here",
        "there",
    }
)
