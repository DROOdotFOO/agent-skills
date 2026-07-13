"""Thin REST client for the Regen incident API.

Auth/URL construction are pure functions (``build_url`` / ``build_auth_kwargs``)
so they can be unit-tested without a network. The request methods themselves are
thin wrappers over ``shared.http.fetch_json`` and are not unit-tested (same
convention as ``sentinel.monitor.fetch_transactions``).
"""

from __future__ import annotations

from typing import Any

from shared.http import fetch_json

from regen.config import RegenConfig
from regen.models import AlertSummary, CorrelationKeys, Incident, IncidentDetail
from regen.parse import (
    extract_correlation_keys,
    extract_items,
    parse_alert,
    parse_incident,
    parse_incident_detail,
)


def build_url(base_url: str, path: str) -> str:
    """Join a configured base URL with an API path.

    Raises ``ValueError`` when no base URL is configured so callers surface a
    clear "set REGEN_BASE_URL" message rather than hitting a malformed URL.
    """
    if not base_url:
        raise ValueError("REGEN_BASE_URL is not set (e.g. http://mini-axol.tail9b2ce8.ts.net:PORT)")
    return f"{base_url}{path}"


def build_auth_kwargs(config: RegenConfig) -> dict[str, Any]:
    """Build httpx auth kwargs from config (cookie -> bearer -> open mode)."""
    if config.session_cookie:
        return {"cookies": {"oi_session": config.session_cookie}}
    if config.api_token:
        return {"headers": {"Authorization": f"Bearer {config.api_token}"}}
    return {}


class RegenClient:
    """Reads (and optionally writes) incidents from a Regen instance."""

    def __init__(self, config: RegenConfig) -> None:
        self.config = config

    def _request_kwargs(self, **extra: Any) -> dict[str, Any]:
        return {**build_auth_kwargs(self.config), "timeout": self.config.timeout, **extra}

    def list_incidents(
        self,
        *,
        status: str | None = None,
        severity: str | None = None,
        created_after: str | None = None,
        created_before: str | None = None,
        limit: int = 20,
    ) -> list[Incident]:
        """List incidents, newest-envelope order, sliced to ``limit``."""
        url = build_url(self.config.base_url, "/api/v1/incidents")
        params = {
            k: v
            for k, v in {
                "status": status,
                "severity": severity,
                "created_after": created_after,
                "created_before": created_before,
            }.items()
            if v
        }
        payload = fetch_json(url, default={}, **self._request_kwargs(params=params))
        incidents = [parse_incident(item) for item in extract_items(payload)]
        return incidents[:limit] if limit and limit > 0 else incidents

    def get_incident(self, incident_id: str | int) -> IncidentDetail | None:
        """Fetch one incident by id or number, with alerts + timeline."""
        url = build_url(self.config.base_url, f"/api/v1/incidents/{incident_id}")
        payload = fetch_json(url, default=None, **self._request_kwargs())
        if not isinstance(payload, dict):
            return None
        return parse_incident_detail(payload)

    def list_alerts(
        self,
        *,
        status: str | None = None,
        source: str | None = None,
        limit: int = 20,
    ) -> list[AlertSummary]:
        """List ingested alerts, sliced to ``limit``."""
        url = build_url(self.config.base_url, "/api/v1/alerts")
        params = {k: v for k, v in {"status": status, "source": source}.items() if v}
        payload = fetch_json(url, default={}, **self._request_kwargs(params=params))
        alerts = [parse_alert(item) for item in extract_items(payload)]
        return alerts[:limit] if limit and limit > 0 else alerts

    def correlation_keys(self, incident_id: str | int) -> CorrelationKeys | None:
        """Fetch an incident and extract SigNoz-query join keys."""
        detail = self.get_incident(incident_id)
        if detail is None:
            return None
        return extract_correlation_keys(detail)

    def patch_incident(
        self,
        incident_id: str | int,
        *,
        status: str | None = None,
        severity: str | None = None,
        summary: str | None = None,
    ) -> IncidentDetail | None:
        """Update an incident (status/severity/summary). Write operation."""
        url = build_url(self.config.base_url, f"/api/v1/incidents/{incident_id}")
        body = {
            k: v
            for k, v in {"status": status, "severity": severity, "summary": summary}.items()
            if v is not None
        }
        payload = fetch_json(url, method="PATCH", default=None, **self._request_kwargs(json=body))
        if not isinstance(payload, dict):
            return None
        return parse_incident_detail(payload)
