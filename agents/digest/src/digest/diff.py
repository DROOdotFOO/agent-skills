"""Differential digest -- classify items as new, ongoing, or declining."""

from __future__ import annotations

from enum import Enum

from digest.memory import FeedMemory
from digest.models import DigestResult, Item


class Trend(str, Enum):
    """Item trend classification."""

    NEW = "new"
    ONGOING = "ongoing"
    ACCELERATING = "accelerating"
    DECLINING = "declining"


def classify_items(
    result: DigestResult,
    memory: FeedMemory,
) -> dict[str, list[tuple[Item, Trend]]]:
    """Classify each item in a digest result by its trend.

    Returns a dict keyed by trend value, each containing (item, trend) tuples.
    """
    previous = memory.previous_urls(result.topic)
    classified: dict[str, list[tuple[Item, Trend]]] = {
        Trend.NEW: [],
        Trend.ACCELERATING: [],
        Trend.ONGOING: [],
        Trend.DECLINING: [],
    }

    for item in result.items:
        if item.url not in previous:
            classified[Trend.NEW].append((item, Trend.NEW))
            continue

        trend_data = memory.engagement_trend(result.topic, item.url)
        if len(trend_data) < 2:
            classified[Trend.ONGOING].append((item, Trend.ONGOING))
            continue

        prev_avg = sum(trend_data) / len(trend_data)
        current = item.engagement

        if prev_avg == 0:
            classified[Trend.NEW].append((item, Trend.NEW))
        elif current > prev_avg * 1.3:
            classified[Trend.ACCELERATING].append((item, Trend.ACCELERATING))
        elif current < prev_avg * 0.5:
            classified[Trend.DECLINING].append((item, Trend.DECLINING))
        else:
            classified[Trend.ONGOING].append((item, Trend.ONGOING))

    return classified


def format_differential(
    classified: dict[str, list[tuple[Item, Trend]]],
) -> str:
    """Format classified items into a differential digest section."""
    sections: list[str] = []

    if classified[Trend.NEW]:
        lines = ["## New since last digest\n"]
        for item, _ in classified[Trend.NEW]:
            lines.append(f"- [{item.source}] [{item.title}]({item.url})")
        sections.append("\n".join(lines))

    if classified[Trend.ACCELERATING]:
        lines = ["## Accelerating\n"]
        for item, _ in classified[Trend.ACCELERATING]:
            lines.append(f"- [{item.source}] [{item.title}]({item.url}) -- gaining momentum")
        sections.append("\n".join(lines))

    if classified[Trend.ONGOING]:
        lines = ["## Ongoing\n"]
        for item, _ in classified[Trend.ONGOING]:
            lines.append(f"- [{item.source}] [{item.title}]({item.url})")
        sections.append("\n".join(lines))

    if classified[Trend.DECLINING]:
        lines = ["## Declining\n"]
        for item, _ in classified[Trend.DECLINING]:
            lines.append(f"- [{item.source}] [{item.title}]({item.url}) -- fading")
        sections.append("\n".join(lines))

    return "\n\n".join(sections) if sections else "No items to classify."
