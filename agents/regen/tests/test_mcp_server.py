"""Tests for the Regen MCP server factory and formatting helpers."""

from __future__ import annotations

import asyncio

import pytest
from fastmcp import FastMCP

from regen.mcp_server import (
    _format_correlation,
    _format_incidents,
    create_server,
)
from regen.models import CorrelationKeys, Incident

READ_TOOLS = frozenset(
    {
        "regen_list_incidents",
        "regen_get_incident",
        "regen_list_alerts",
        "regen_correlation_keys",
    }
)
WRITE_TOOLS = frozenset(
    {
        "regen_ack_incident",
        "regen_resolve_incident",
        "regen_update_incident",
    }
)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv("REGEN_ENABLE_WRITE", raising=False)
    monkeypatch.delenv("REGEN_BASE_URL", raising=False)


def _tool_names(server: FastMCP) -> set[str]:
    return {t.name for t in asyncio.run(server.list_tools())}


def test_create_server_returns_fastmcp():
    assert isinstance(create_server(), FastMCP)


def test_read_only_tool_set():
    names = _tool_names(create_server())
    assert names == READ_TOOLS


def test_write_mode_tool_set():
    names = _tool_names(create_server(enable_write=True))
    assert names == READ_TOOLS | WRITE_TOOLS


def test_write_mode_from_env(monkeypatch):
    monkeypatch.setenv("REGEN_ENABLE_WRITE", "1")
    names = _tool_names(create_server())
    assert names == READ_TOOLS | WRITE_TOOLS


# --- formatting helpers ---


def test_format_incidents_empty():
    assert _format_incidents([]) == "No incidents."


def test_format_incidents_lists_number_and_title():
    out = _format_incidents([Incident(incident_number=42, title="Gas low", severity="critical")])
    assert "#42" in out
    assert "Gas low" in out
    assert "CRITICAL" in out


def test_format_correlation_renders_hint():
    keys = CorrelationKeys(
        incident_id="x",
        incident_number=42,
        title="Gas low",
        status="triggered",
        severity="critical",
        service_names=["riddler-production"],
        labels={"chain": "base"},
        signoz_hint="service.name IN (riddler-production) AND chain='base'",
    )
    out = _format_correlation(keys)
    assert "#42" in out
    assert "riddler-production" in out
    assert "chain='base'" in out
