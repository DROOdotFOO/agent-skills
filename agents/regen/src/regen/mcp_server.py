"""FastMCP server exposing Regen incident tools for Claude Code integration.

Read tools are always registered. Write tools (ack/resolve/update) are only
registered when write mode is enabled (``REGEN_ENABLE_WRITE=1`` or the
``enable_write`` argument), mirroring the PagerDuty MCP's ``--enable-write-tools``.
"""

from __future__ import annotations

from datetime import datetime

from fastmcp import FastMCP

from regen.client import RegenClient
from regen.config import RegenConfig
from regen.models import (
    AlertSummary,
    CorrelationKeys,
    Incident,
    IncidentDetail,
)


def _ts(value: datetime | None) -> str:
    return value.isoformat() if value else "-"


def _format_incident_line(inc: Incident) -> str:
    return (
        f"#{inc.incident_number} [{inc.severity.upper() or '?'}/{inc.status or '?'}] "
        f"{inc.title}  (id={inc.id})"
    )


def _format_incidents(incidents: list[Incident]) -> str:
    if not incidents:
        return "No incidents."
    lines = [f"{len(incidents)} incident(s):", ""]
    lines.extend(_format_incident_line(inc) for inc in incidents)
    return "\n".join(lines)


def _format_incident_detail(detail: IncidentDetail) -> str:
    lines = [
        _format_incident_line(detail),
        f"  triggered: {_ts(detail.triggered_at)}  ack: {_ts(detail.acknowledged_at)}  "
        f"resolved: {_ts(detail.resolved_at)}",
    ]
    if detail.commander_name:
        lines.append(f"  commander: {detail.commander_name}")
    if detail.summary:
        lines.append(f"  summary: {detail.summary}")
    if detail.ai_summary:
        lines.append(f"  ai_summary: {detail.ai_summary}")
    if detail.alerts:
        lines.append(f"  alerts ({len(detail.alerts)}):")
        for alert in detail.alerts:
            label_str = ", ".join(f"{k}={v}" for k, v in alert.labels.items())
            lines.append(f"    - [{alert.source}] {alert.title} {{{label_str}}}")
    return "\n".join(lines)


def _format_alerts(alerts: list[AlertSummary]) -> str:
    if not alerts:
        return "No alerts."
    lines = [f"{len(alerts)} alert(s):", ""]
    for alert in alerts:
        label_str = ", ".join(f"{k}={v}" for k, v in alert.labels.items())
        lines.append(
            f"[{alert.severity.upper() or '?'}/{alert.status or '?'}] "
            f"{alert.title} ({alert.source})  {{{label_str}}}  id={alert.id}"
        )
    return "\n".join(lines)


def _format_correlation(keys: CorrelationKeys) -> str:
    lines = [
        f"Correlation keys for incident #{keys.incident_number} ({keys.title}):",
        f"  status={keys.status}  severity={keys.severity}",
        f"  window: {_ts(keys.window_start)}  ->  {_ts(keys.window_end)}",
    ]
    if keys.service_names:
        lines.append(f"  service.name: {', '.join(keys.service_names)}")
    if keys.labels:
        lines.append("  labels:")
        lines.extend(f"    {k} = {v}" for k, v in keys.labels.items())
    lines.append("")
    lines.append("SigNoz query hint (feed into the signoz MCP):")
    lines.append(f"  {keys.signoz_hint}")
    return "\n".join(lines)


def create_server(enable_write: bool | None = None) -> FastMCP:
    """Create a FastMCP server exposing Regen incident tools.

    Args:
        enable_write: register write tools (ack/resolve/update). When ``None``,
            resolved from ``REGEN_ENABLE_WRITE``.
    """
    config = RegenConfig.from_env()
    if enable_write is None:
        enable_write = config.enable_write
    client = RegenClient(config)

    mcp = FastMCP(
        "regen",
        instructions=(
            "Read Fluidify Regen incidents/alerts and correlate them with SigNoz OTel. "
            "Use regen_list_incidents / regen_get_incident to inspect incidents, and "
            "regen_correlation_keys to extract service.name + labels + a time window to "
            "feed into the signoz MCP. Set REGEN_BASE_URL to the Regen instance URL."
        ),
    )

    @mcp.tool()
    def regen_list_incidents(
        status: str | None = None,
        severity: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        limit: int = 20,
    ) -> str:
        """List Regen incidents.

        Args:
            status: Filter by status (triggered, acknowledged, resolved, canceled).
            severity: Filter by severity (critical, high, medium, low).
            created_after: RFC3339 lower bound on creation time (optional).
            created_before: RFC3339 upper bound on creation time (optional).
            limit: Max incidents to return (default 20).
        """
        try:
            incidents = client.list_incidents(
                status=status,
                severity=severity,
                created_after=created_after,
                created_before=created_before,
                limit=limit,
            )
        except Exception as exc:
            return f"Error listing incidents: {exc}"
        return _format_incidents(incidents)

    @mcp.tool()
    def regen_get_incident(incident_id: str) -> str:
        """Get a single Regen incident by id or incident number, with alerts + timeline.

        Args:
            incident_id: Incident UUID or incident number.
        """
        try:
            detail = client.get_incident(incident_id)
        except Exception as exc:
            return f"Error fetching incident: {exc}"
        if detail is None:
            return f"Incident {incident_id} not found."
        return _format_incident_detail(detail)

    @mcp.tool()
    def regen_list_alerts(
        status: str | None = None,
        source: str | None = None,
        limit: int = 20,
    ) -> str:
        """List ingested Regen alerts.

        Args:
            status: Filter by alert status (optional).
            source: Filter by source (e.g. prometheus, grafana, generic) (optional).
            limit: Max alerts to return (default 20).
        """
        try:
            alerts = client.list_alerts(status=status, source=source, limit=limit)
        except Exception as exc:
            return f"Error listing alerts: {exc}"
        return _format_alerts(alerts)

    @mcp.tool()
    def regen_correlation_keys(incident_id: str) -> str:
        """Extract SigNoz-query join keys (service.name, labels, time window) from an incident.

        Pull these from a Regen incident, then query the signoz MCP with the
        service.name / labels / window to find the matching OTel traces & metrics.

        Args:
            incident_id: Incident UUID or incident number.
        """
        try:
            keys = client.correlation_keys(incident_id)
        except Exception as exc:
            return f"Error extracting correlation keys: {exc}"
        if keys is None:
            return f"Incident {incident_id} not found."
        return _format_correlation(keys)

    if enable_write:

        @mcp.tool()
        def regen_ack_incident(incident_id: str) -> str:
            """Acknowledge a Regen incident (write).

            Args:
                incident_id: Incident UUID or incident number.
            """
            try:
                detail = client.patch_incident(incident_id, status="acknowledged")
            except Exception as exc:
                return f"Error acknowledging incident: {exc}"
            if detail is None:
                return f"Incident {incident_id} not found or update failed."
            return "Acknowledged.\n" + _format_incident_detail(detail)

        @mcp.tool()
        def regen_resolve_incident(incident_id: str, summary: str | None = None) -> str:
            """Resolve a Regen incident, optionally setting a summary (write).

            Args:
                incident_id: Incident UUID or incident number.
                summary: Optional resolution summary.
            """
            try:
                detail = client.patch_incident(incident_id, status="resolved", summary=summary)
            except Exception as exc:
                return f"Error resolving incident: {exc}"
            if detail is None:
                return f"Incident {incident_id} not found or update failed."
            return "Resolved.\n" + _format_incident_detail(detail)

        @mcp.tool()
        def regen_update_incident(
            incident_id: str,
            status: str | None = None,
            severity: str | None = None,
            summary: str | None = None,
        ) -> str:
            """Update a Regen incident's status, severity, and/or summary (write).

            Args:
                incident_id: Incident UUID or incident number.
                status: New status (triggered, acknowledged, resolved, canceled).
                severity: New severity (critical, high, medium, low).
                summary: New summary text.
            """
            try:
                detail = client.patch_incident(
                    incident_id, status=status, severity=severity, summary=summary
                )
            except Exception as exc:
                return f"Error updating incident: {exc}"
            if detail is None:
                return f"Incident {incident_id} not found or update failed."
            return "Updated.\n" + _format_incident_detail(detail)

    return mcp
