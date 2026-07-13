"""Tests for Regen pydantic models and enums."""

from __future__ import annotations

from regen.models import (
    AlertSummary,
    CorrelationKeys,
    Incident,
    IncidentDetail,
    IncidentStatus,
    Severity,
)


def test_status_enum_values():
    assert IncidentStatus.TRIGGERED.value == "triggered"
    assert IncidentStatus.RESOLVED.value == "resolved"
    assert {s.value for s in IncidentStatus} == {
        "triggered",
        "acknowledged",
        "resolved",
        "canceled",
    }


def test_severity_enum_values():
    assert Severity.CRITICAL.value == "critical"
    assert {s.value for s in Severity} == {"critical", "high", "medium", "low"}


def test_incident_defaults():
    inc = Incident()
    assert inc.incident_number == 0
    assert inc.ai_enabled is False
    assert inc.group_key is None


def test_alert_summary_defaults():
    alert = AlertSummary()
    assert alert.labels == {}
    assert alert.received_at is None


def test_incident_detail_is_incident():
    detail = IncidentDetail(incident_number=7)
    assert isinstance(detail, Incident)
    assert detail.alerts == []
    assert detail.timeline == []


def test_correlation_keys_required_fields():
    keys = CorrelationKeys(
        incident_id="x",
        incident_number=1,
        title="t",
        status="triggered",
        severity="critical",
    )
    assert keys.service_names == []
    assert keys.labels == {}
