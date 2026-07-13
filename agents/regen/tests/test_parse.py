"""Tests for Regen JSON parsing and correlation-key extraction."""

from __future__ import annotations

from regen.parse import (
    _parse_ts,
    extract_correlation_keys,
    extract_items,
    parse_alert,
    parse_incident,
    parse_incident_detail,
)

DETAIL = {
    "id": "uuid-1",
    "incident_number": 42,
    "title": "Solver gas low on Base",
    "slug": "solver-gas-low-on-base",
    "status": "triggered",
    "severity": "critical",
    "summary": "gas < 0.0005",
    "created_at": "2026-07-13T10:00:00Z",
    "triggered_at": "2026-07-13T10:00:01.123456789Z",
    "ai_enabled": True,
    "alerts": [
        {
            "id": "a1",
            "title": "SolverGasLowBase",
            "source": "prometheus",
            "severity": "critical",
            "status": "firing",
            "labels": {
                "service.name": "riddler-production",
                "chain": "base",
                "role": "solver",
                "address": "0x97D4",
                "intent_id": "i-1",
                "alertname": "SolverGasLowBase",
            },
            "received_at": "2026-07-13T10:00:00Z",
        },
        {
            "id": "a2",
            "title": "extra",
            "source": "generic",
            "severity": "warning",
            "status": "firing",
            "labels": {"service_name": "riddler-balance-exporter", "chain": "base"},
        },
    ],
    "timeline": [
        {
            "id": "t1",
            "timestamp": "2026-07-13T10:00:02Z",
            "type": "triggered",
            "actor_type": "system",
            "content": {},
        }
    ],
}


# --- extract_items ---


def test_extract_items_data_key():
    assert extract_items({"data": [{"id": "1"}, {"id": "2"}]}) == [{"id": "1"}, {"id": "2"}]


def test_extract_items_items_key():
    assert extract_items({"items": [{"id": "1"}]}) == [{"id": "1"}]


def test_extract_items_bare_list():
    assert extract_items([{"id": "1"}]) == [{"id": "1"}]


def test_extract_items_empty_dict():
    assert extract_items({}) == []


def test_extract_items_none():
    assert extract_items(None) == []


def test_extract_items_drops_non_dicts():
    assert extract_items({"data": [{"id": "1"}, "junk", 3]}) == [{"id": "1"}]


# --- _parse_ts ---


def test_parse_ts_nanoseconds():
    dt = _parse_ts("2026-07-13T10:00:01.123456789Z")
    assert dt is not None
    assert dt.year == 2026 and dt.month == 7


def test_parse_ts_plain_z():
    dt = _parse_ts("2026-07-13T10:00:00Z")
    assert dt is not None and dt.tzinfo is not None


def test_parse_ts_none():
    assert _parse_ts(None) is None


def test_parse_ts_garbage():
    assert _parse_ts("not-a-time") is None


# --- parse_incident ---


def test_parse_incident_fields():
    inc = parse_incident(DETAIL)
    assert inc.incident_number == 42
    assert inc.status == "triggered"
    assert inc.severity == "critical"
    assert inc.ai_enabled is True
    assert inc.group_key is None
    assert inc.triggered_at is not None


def test_parse_incident_missing_fields_defaults():
    inc = parse_incident({})
    assert inc.incident_number == 0
    assert inc.title == ""
    assert inc.ai_enabled is False


# --- parse_alert ---


def test_parse_alert_preserves_labels():
    alert = parse_alert(DETAIL["alerts"][0])
    assert alert.labels["service.name"] == "riddler-production"
    assert alert.source == "prometheus"


def test_parse_alert_missing_labels():
    alert = parse_alert({"id": "x", "title": "t"})
    assert alert.labels == {}


# --- parse_incident_detail ---


def test_parse_incident_detail_nested():
    detail = parse_incident_detail(DETAIL)
    assert len(detail.alerts) == 2
    assert len(detail.timeline) == 1
    assert detail.alerts[0].title == "SolverGasLowBase"


def test_parse_incident_detail_no_children():
    detail = parse_incident_detail({"id": "x", "incident_number": 1})
    assert detail.alerts == []
    assert detail.timeline == []


# --- extract_correlation_keys ---


def test_correlation_service_names_deduped_ordered():
    keys = extract_correlation_keys(parse_incident_detail(DETAIL))
    assert keys.service_names == ["riddler-production", "riddler-balance-exporter"]


def test_correlation_labels_merged():
    keys = extract_correlation_keys(parse_incident_detail(DETAIL))
    assert keys.labels["chain"] == "base"
    assert keys.labels["role"] == "solver"
    assert keys.labels["intent_id"] == "i-1"
    assert keys.labels["address"] == "0x97D4"


def test_correlation_window():
    detail = parse_incident_detail(DETAIL)
    keys = extract_correlation_keys(detail)
    assert keys.window_start == detail.triggered_at
    assert keys.window_end is not None
    assert keys.window_end >= keys.window_start


def test_correlation_signoz_hint():
    keys = extract_correlation_keys(parse_incident_detail(DETAIL))
    assert "service.name IN (riddler-production, riddler-balance-exporter)" in keys.signoz_hint
    assert "chain='base'" in keys.signoz_hint
    assert "severity=critical" in keys.signoz_hint


def test_correlation_no_alerts_is_safe():
    keys = extract_correlation_keys(parse_incident_detail({"id": "x", "incident_number": 1}))
    assert keys.service_names == []
    assert keys.labels == {}
    assert keys.signoz_hint  # still emits a time-bounded hint
