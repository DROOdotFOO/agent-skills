"""Pure parsers: Regen API JSON -> pydantic models, and correlation extraction.

Kept free of network/IO so they can be unit-tested against synthetic JSON
(the same approach as ``sentinel.monitor._parse_transaction``).
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from shared.dates import parse_iso_utc

from regen.models import (
    AlertSummary,
    CorrelationKeys,
    Incident,
    IncidentDetail,
    TimelineEntry,
)

# Label keys (normalized: lowercased, dots -> underscores) worth surfacing when
# correlating a Regen incident against SigNoz OTel. Sourced from the riddler
# otel-collector spanmetrics dimensions + balance-exporter labels.
_KNOWN_LABEL_KEYS = frozenset(
    {
        "service_name",
        "service",
        "service_namespace",
        "chain",
        "role",
        "address",
        "token",
        "network",
        "intent_id",
        "lifi_intent_id",
        "deposit_id",
        "origin_chain_id",
        "destination_chain_id",
        "sla_status",
        "sla_flow_type",
        "sla_segment",
        "alertname",
        "severity",
        "env",
        "environment",
    }
)

_SERVICE_NAME_KEYS = frozenset({"service_name", "service"})

_FRACTIONAL_TS = re.compile(r"^(.*\.\d{6})\d+(.*)$")


def _parse_ts(value: Any) -> datetime | None:
    """Parse an RFC3339/ISO timestamp, tolerating Go's nanosecond precision."""
    dt = parse_iso_utc(value if isinstance(value, str) else None)
    if dt is not None or not isinstance(value, str):
        return dt
    # Go marshals time.Time with up to 9 fractional digits; fromisoformat on
    # Python < 3.12 rejects that. Truncate to microseconds and retry.
    match = _FRACTIONAL_TS.match(value)
    if match:
        return parse_iso_utc(match.group(1) + match.group(2))
    return None


def _normalize_key(key: str) -> str:
    """Lowercase and replace dots with underscores for label matching."""
    return key.lower().replace(".", "_")


def extract_items(payload: Any) -> list[dict]:
    """Pull the list of records from a Regen paginated envelope.

    Tolerant of the exact shape: accepts ``{"data": [...]}``, ``{"items": [...]}``,
    a bare list, or an empty/None payload.
    """
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("data", "items", "incidents", "alerts", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def parse_incident(raw: dict) -> Incident:
    """Parse a Regen incident summary object."""
    return Incident(
        id=str(raw.get("id", "")),
        incident_number=int(raw.get("incident_number", 0) or 0),
        title=raw.get("title", "") or "",
        slug=raw.get("slug", "") or "",
        status=raw.get("status", "") or "",
        severity=raw.get("severity", "") or "",
        summary=raw.get("summary", "") or "",
        group_key=raw.get("group_key"),
        created_at=_parse_ts(raw.get("created_at")),
        triggered_at=_parse_ts(raw.get("triggered_at")),
        acknowledged_at=_parse_ts(raw.get("acknowledged_at")),
        resolved_at=_parse_ts(raw.get("resolved_at")),
        ai_summary=raw.get("ai_summary"),
        ai_enabled=bool(raw.get("ai_enabled", False)),
        commander_name=raw.get("commander_name", "") or "",
    )


def parse_alert(raw: dict) -> AlertSummary:
    """Parse an embedded alert-summary object."""
    labels = raw.get("labels")
    if not isinstance(labels, dict):
        labels = {}
    return AlertSummary(
        id=str(raw.get("id", "")),
        title=raw.get("title", "") or "",
        source=raw.get("source", "") or "",
        severity=raw.get("severity", "") or "",
        status=raw.get("status", "") or "",
        labels=labels,
        received_at=_parse_ts(raw.get("received_at")),
    )


def parse_timeline_entry(raw: dict) -> TimelineEntry:
    """Parse a single timeline entry."""
    content = raw.get("content")
    if not isinstance(content, dict):
        content = {}
    return TimelineEntry(
        id=str(raw.get("id", "")),
        timestamp=_parse_ts(raw.get("timestamp")),
        type=raw.get("type", "") or "",
        actor_type=raw.get("actor_type", "") or "",
        actor_name=raw.get("actor_name", "") or "",
        content=content,
    )


def parse_incident_detail(raw: dict) -> IncidentDetail:
    """Parse a full incident-detail object (incident + alerts + timeline)."""
    base = parse_incident(raw)
    alerts_raw = raw.get("alerts") if isinstance(raw.get("alerts"), list) else []
    timeline_raw = raw.get("timeline") if isinstance(raw.get("timeline"), list) else []
    return IncidentDetail(
        **base.model_dump(),
        alerts=[parse_alert(a) for a in alerts_raw if isinstance(a, dict)],
        timeline=[parse_timeline_entry(t) for t in timeline_raw if isinstance(t, dict)],
    )


def _merge_labels(detail: IncidentDetail) -> dict[str, str]:
    """Merge known correlation labels across all of an incident's alerts."""
    merged: dict[str, str] = {}
    for alert in detail.alerts:
        for key, value in alert.labels.items():
            norm = _normalize_key(str(key))
            if norm in _KNOWN_LABEL_KEYS and value is not None:
                merged.setdefault(norm, str(value))
    return merged


def extract_correlation_keys(detail: IncidentDetail) -> CorrelationKeys:
    """Derive SigNoz-query join keys + a filter hint from an incident's alerts.

    Pairs with the ``signoz`` MCP: the returned ``signoz_hint`` and
    ``service_names`` map onto ``service.name`` and label filters, and the window
    onto the query time range.
    """
    labels = _merge_labels(detail)

    service_names: list[str] = []
    for alert in detail.alerts:
        for key, value in alert.labels.items():
            if _normalize_key(str(key)) in _SERVICE_NAME_KEYS and value:
                name = str(value)
                if name not in service_names:
                    service_names.append(name)

    window_start = detail.triggered_at or detail.created_at
    window_end = detail.resolved_at or datetime.now(timezone.utc)

    hint_parts: list[str] = []
    if service_names:
        joined = ", ".join(service_names)
        hint_parts.append(f"service.name IN ({joined})")
    for key in ("chain", "role", "network"):
        if key in labels:
            hint_parts.append(f"{key}='{labels[key]}'")
    if window_start is not None:
        hint_parts.append(f"time>={window_start.isoformat()}")
    hint_parts.append(f"time<={window_end.isoformat()}")
    if detail.severity:
        hint_parts.append(f"(incident severity={detail.severity})")
    signoz_hint = " AND ".join(hint_parts)

    return CorrelationKeys(
        incident_id=detail.id,
        incident_number=detail.incident_number,
        title=detail.title,
        status=detail.status,
        severity=detail.severity,
        service_names=service_names,
        labels=labels,
        window_start=window_start,
        window_end=window_end,
        signoz_hint=signoz_hint,
    )
