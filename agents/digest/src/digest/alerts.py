"""Alert thresholds and trigger rules for digest watch mode.

Evaluates digest results against configurable thresholds and fires alerts
when conditions are met. Trigger rules detect domain-specific patterns
like new governance proposals or engagement spikes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field

from digest.credibility import Tier, source_tier
from digest.diff import Trend, classify_items
from digest.memory import FeedMemory
from digest.models import DigestResult, Item


class AlertSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class DigestAlert(BaseModel):
    """A single alert fired by the digest watch system."""

    topic: str
    severity: AlertSeverity
    rule: str
    message: str
    items: list[str] = Field(default_factory=list, description="URLs of triggering items")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AlertThresholds(BaseModel):
    """Configurable thresholds for a watched topic."""

    min_engagement: int = 0
    min_new_items: int = 0
    accelerating_count: int = 0
    credibility_floor: str = ""  # "", "verified", "deliberate", "passive"


class TriggerConfig(BaseModel):
    """Domain-specific trigger rules for a watched topic."""

    new_governance_proposal: bool = False
    dependency_spike_factor: float = 0.0  # 0 = disabled, 2.0 = 2x previous


# ---------------------------------------------------------------------------
# Threshold evaluation
# ---------------------------------------------------------------------------


def evaluate_thresholds(
    result: DigestResult,
    thresholds: AlertThresholds,
    memory: FeedMemory | None = None,
) -> list[DigestAlert]:
    """Evaluate a digest result against alert thresholds.

    Returns a list of alerts for any thresholds that were crossed.
    """
    alerts: list[DigestAlert] = []

    # Engagement threshold: items above min_engagement
    if thresholds.min_engagement > 0:
        hot = [i for i in result.items if i.engagement >= thresholds.min_engagement]
        if hot:
            alerts.append(
                DigestAlert(
                    topic=result.topic,
                    severity=AlertSeverity.MEDIUM,
                    rule="engagement_threshold",
                    message=(
                        f"{len(hot)} item(s) crossed engagement threshold "
                        f"({thresholds.min_engagement})"
                    ),
                    items=[i.url for i in hot],
                )
            )

    # Credibility floor: only alert on items at or above a tier
    if thresholds.credibility_floor:
        floor = _parse_tier(thresholds.credibility_floor)
        if floor is not None:
            tier_order = {Tier.VERIFIED: 3, Tier.DELIBERATE: 2, Tier.PASSIVE: 1}
            floor_rank = tier_order.get(floor, 0)
            credible = [
                i for i in result.items if tier_order.get(source_tier(i.source), 0) >= floor_rank
            ]
            if credible:
                alerts.append(
                    DigestAlert(
                        topic=result.topic,
                        severity=AlertSeverity.LOW,
                        rule="credibility_floor",
                        message=(
                            f"{len(credible)} item(s) from {thresholds.credibility_floor}+ "
                            f"tier sources"
                        ),
                        items=[i.url for i in credible],
                    )
                )

    # Differential thresholds require feed memory
    if memory and (thresholds.min_new_items > 0 or thresholds.accelerating_count > 0):
        classified = classify_items(result, memory)

        if thresholds.min_new_items > 0:
            new_items = classified.get(Trend.NEW, [])
            if len(new_items) >= thresholds.min_new_items:
                alerts.append(
                    DigestAlert(
                        topic=result.topic,
                        severity=AlertSeverity.HIGH,
                        rule="new_items_threshold",
                        message=(
                            f"{len(new_items)} new item(s) since last digest "
                            f"(threshold: {thresholds.min_new_items})"
                        ),
                        items=[i.url for i, _ in new_items],
                    )
                )

        if thresholds.accelerating_count > 0:
            accel = classified.get(Trend.ACCELERATING, [])
            if len(accel) >= thresholds.accelerating_count:
                alerts.append(
                    DigestAlert(
                        topic=result.topic,
                        severity=AlertSeverity.HIGH,
                        rule="accelerating_threshold",
                        message=(
                            f"{len(accel)} item(s) accelerating "
                            f"(threshold: {thresholds.accelerating_count})"
                        ),
                        items=[i.url for i, _ in accel],
                    )
                )

    return alerts


# ---------------------------------------------------------------------------
# Trigger rules
# ---------------------------------------------------------------------------


def check_governance_trigger(result: DigestResult) -> list[DigestAlert]:
    """Fire alerts for new governance proposals (Snapshot).

    Detects proposals in 'active' or 'pending' state from the snapshot adapter.
    """
    alerts: list[DigestAlert] = []
    proposals = [
        i
        for i in result.items
        if i.source == "snapshot" and i.raw.get("state") in ("active", "pending")
    ]
    if proposals:
        alerts.append(
            DigestAlert(
                topic=result.topic,
                severity=AlertSeverity.HIGH,
                rule="new_governance_proposal",
                message=f"{len(proposals)} active governance proposal(s) detected",
                items=[p.url for p in proposals],
            )
        )
    return alerts


def check_dependency_spike(
    result: DigestResult,
    factor: float,
    memory: FeedMemory,
) -> list[DigestAlert]:
    """Fire alerts when a package item's engagement spikes relative to history.

    Args:
        factor: Multiplier threshold (e.g. 2.0 = 2x previous average).
    """
    if factor <= 0:
        return []

    alerts: list[DigestAlert] = []
    pkg_items = [i for i in result.items if i.source in ("packages", "github")]
    spiking: list[Item] = []

    for item in pkg_items:
        trend = memory.engagement_trend(result.topic, item.url)
        if len(trend) < 2:
            continue
        prev_avg = sum(trend) / len(trend)
        if prev_avg > 0 and item.engagement > prev_avg * factor:
            spiking.append(item)

    if spiking:
        alerts.append(
            DigestAlert(
                topic=result.topic,
                severity=AlertSeverity.MEDIUM,
                rule="dependency_spike",
                message=(
                    f"{len(spiking)} dependency item(s) spiking >{factor}x previous engagement"
                ),
                items=[i.url for i in spiking],
            )
        )
    return alerts


def evaluate_triggers(
    result: DigestResult,
    triggers: TriggerConfig,
    memory: FeedMemory | None = None,
) -> list[DigestAlert]:
    """Run all configured trigger rules against a digest result."""
    alerts: list[DigestAlert] = []

    if triggers.new_governance_proposal:
        alerts.extend(check_governance_trigger(result))

    if triggers.dependency_spike_factor > 0 and memory:
        alerts.extend(check_dependency_spike(result, triggers.dependency_spike_factor, memory))

    return alerts


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_TIER_NAMES = {
    "verified": Tier.VERIFIED,
    "deliberate": Tier.DELIBERATE,
    "passive": Tier.PASSIVE,
}


def _parse_tier(name: str) -> Tier | None:
    return _TIER_NAMES.get(name.lower())
