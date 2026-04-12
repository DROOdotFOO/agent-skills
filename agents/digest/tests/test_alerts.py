"""Tests for alert thresholds and trigger rules."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from digest.alerts import (
    AlertSeverity,
    AlertThresholds,
    TriggerConfig,
    check_dependency_spike,
    check_governance_trigger,
    evaluate_thresholds,
    evaluate_triggers,
)
from digest.memory import FeedMemory
from digest.models import DigestResult, Item


def _item(
    url: str = "https://a.com",
    source: str = "hn",
    engagement: int = 100,
    raw: dict | None = None,
) -> Item:
    return Item(
        source=source,
        title=f"Item {url}",
        url=url,
        timestamp=datetime.now(timezone.utc),
        engagement=engagement,
        raw=raw or {},
    )


def _result(items: list[Item], topic: str = "test") -> DigestResult:
    return DigestResult(topic=topic, days=30, items=items, narrative="n/a")


@pytest.fixture()
def mem(tmp_path: Path) -> FeedMemory:
    return FeedMemory(db_path=tmp_path / "test_feed.db")


# -- Engagement threshold --


class TestEngagementThreshold:
    def test_fires_when_engagement_exceeds_threshold(self) -> None:
        result = _result([_item(engagement=200), _item(url="https://b.com", engagement=50)])
        thresholds = AlertThresholds(min_engagement=100)
        alerts = evaluate_thresholds(result, thresholds)
        assert len(alerts) == 1
        assert alerts[0].rule == "engagement_threshold"
        assert "1 item(s)" in alerts[0].message

    def test_no_alert_below_threshold(self) -> None:
        result = _result([_item(engagement=50)])
        thresholds = AlertThresholds(min_engagement=100)
        alerts = evaluate_thresholds(result, thresholds)
        assert len(alerts) == 0

    def test_disabled_when_zero(self) -> None:
        result = _result([_item(engagement=9999)])
        thresholds = AlertThresholds(min_engagement=0)
        alerts = evaluate_thresholds(result, thresholds)
        engagement_alerts = [a for a in alerts if a.rule == "engagement_threshold"]
        assert len(engagement_alerts) == 0


# -- Credibility floor --


class TestCredibilityFloor:
    def test_verified_floor_includes_snapshot(self) -> None:
        result = _result(
            [
                _item(source="snapshot", engagement=10),
                _item(url="https://b.com", source="youtube", engagement=10),
            ]
        )
        thresholds = AlertThresholds(credibility_floor="verified")
        alerts = evaluate_thresholds(result, thresholds)
        cred_alerts = [a for a in alerts if a.rule == "credibility_floor"]
        assert len(cred_alerts) == 1
        assert "1 item(s)" in cred_alerts[0].message

    def test_deliberate_floor_includes_hn_and_verified(self) -> None:
        result = _result(
            [
                _item(source="hn", engagement=10),
                _item(url="https://b.com", source="snapshot", engagement=10),
                _item(url="https://c.com", source="youtube", engagement=10),
            ]
        )
        thresholds = AlertThresholds(credibility_floor="deliberate")
        alerts = evaluate_thresholds(result, thresholds)
        cred_alerts = [a for a in alerts if a.rule == "credibility_floor"]
        assert len(cred_alerts) == 1
        assert "2 item(s)" in cred_alerts[0].message

    def test_empty_floor_disabled(self) -> None:
        result = _result([_item(source="snapshot")])
        thresholds = AlertThresholds(credibility_floor="")
        alerts = evaluate_thresholds(result, thresholds)
        cred_alerts = [a for a in alerts if a.rule == "credibility_floor"]
        assert len(cred_alerts) == 0


# -- New items threshold --


class TestNewItemsThreshold:
    def test_fires_when_enough_new_items(self, mem: FeedMemory) -> None:
        # Store a previous digest with different URLs
        mem.store(_result([_item(url="https://old.com")]))

        result = _result(
            [
                _item(url="https://new1.com"),
                _item(url="https://new2.com"),
                _item(url="https://new3.com"),
            ]
        )
        thresholds = AlertThresholds(min_new_items=3)
        alerts = evaluate_thresholds(result, thresholds, memory=mem)
        new_alerts = [a for a in alerts if a.rule == "new_items_threshold"]
        assert len(new_alerts) == 1
        assert new_alerts[0].severity == AlertSeverity.HIGH

    def test_no_alert_without_memory(self) -> None:
        result = _result([_item()])
        thresholds = AlertThresholds(min_new_items=1)
        alerts = evaluate_thresholds(result, thresholds, memory=None)
        new_alerts = [a for a in alerts if a.rule == "new_items_threshold"]
        assert len(new_alerts) == 0


# -- Accelerating threshold --


class TestAcceleratingThreshold:
    def test_fires_when_items_accelerate(self, mem: FeedMemory) -> None:
        mem.store(_result([_item(url="https://a.com", engagement=50)]))
        mem.store(_result([_item(url="https://a.com", engagement=60)]))

        result = _result([_item(url="https://a.com", engagement=200)])
        thresholds = AlertThresholds(accelerating_count=1)
        alerts = evaluate_thresholds(result, thresholds, memory=mem)
        accel_alerts = [a for a in alerts if a.rule == "accelerating_threshold"]
        assert len(accel_alerts) == 1


# -- Governance trigger --


class TestGovernanceTrigger:
    def test_fires_on_active_proposal(self) -> None:
        item = _item(
            source="snapshot",
            raw={"state": "active", "space_id": "aave.eth", "votes": 500},
        )
        result = _result([item])
        alerts = check_governance_trigger(result)
        assert len(alerts) == 1
        assert alerts[0].rule == "new_governance_proposal"
        assert alerts[0].severity == AlertSeverity.HIGH

    def test_fires_on_pending_proposal(self) -> None:
        item = _item(source="snapshot", raw={"state": "pending"})
        result = _result([item])
        alerts = check_governance_trigger(result)
        assert len(alerts) == 1

    def test_ignores_closed_proposal(self) -> None:
        item = _item(source="snapshot", raw={"state": "closed"})
        result = _result([item])
        alerts = check_governance_trigger(result)
        assert len(alerts) == 0

    def test_ignores_non_snapshot_items(self) -> None:
        item = _item(source="hn", raw={"state": "active"})
        result = _result([item])
        alerts = check_governance_trigger(result)
        assert len(alerts) == 0


# -- Dependency spike trigger --


class TestDependencySpike:
    def test_fires_on_engagement_spike(self, mem: FeedMemory) -> None:
        pkg = _item(url="https://pkg.com", source="packages", engagement=50)
        mem.store(_result([pkg]))
        mem.store(_result([pkg]))

        spiked = _item(url="https://pkg.com", source="packages", engagement=200)
        result = _result([spiked])
        alerts = check_dependency_spike(result, factor=2.0, memory=mem)
        assert len(alerts) == 1
        assert alerts[0].rule == "dependency_spike"

    def test_no_spike_below_factor(self, mem: FeedMemory) -> None:
        pkg = _item(url="https://pkg.com", source="packages", engagement=50)
        mem.store(_result([pkg]))
        mem.store(_result([pkg]))

        stable = _item(url="https://pkg.com", source="packages", engagement=60)
        result = _result([stable])
        alerts = check_dependency_spike(result, factor=2.0, memory=mem)
        assert len(alerts) == 0

    def test_disabled_when_factor_zero(self, mem: FeedMemory) -> None:
        result = _result([_item(source="packages", engagement=9999)])
        alerts = check_dependency_spike(result, factor=0, memory=mem)
        assert len(alerts) == 0


# -- evaluate_triggers --


class TestEvaluateTriggers:
    def test_governance_trigger_via_config(self) -> None:
        item = _item(source="snapshot", raw={"state": "active"})
        result = _result([item])
        triggers = TriggerConfig(new_governance_proposal=True)
        alerts = evaluate_triggers(result, triggers)
        assert len(alerts) == 1

    def test_dependency_spike_via_config(self, mem: FeedMemory) -> None:
        pkg = _item(url="https://pkg.com", source="packages", engagement=50)
        mem.store(_result([pkg]))
        mem.store(_result([pkg]))

        spiked = _item(url="https://pkg.com", source="packages", engagement=200)
        result = _result([spiked])
        triggers = TriggerConfig(dependency_spike_factor=2.0)
        alerts = evaluate_triggers(result, triggers, memory=mem)
        assert len(alerts) == 1

    def test_no_triggers_when_disabled(self) -> None:
        result = _result([_item(source="snapshot", raw={"state": "active"})])
        triggers = TriggerConfig()
        alerts = evaluate_triggers(result, triggers)
        assert len(alerts) == 0
