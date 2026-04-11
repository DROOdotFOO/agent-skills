"""Tests for the sentinel MCP server factory."""

from __future__ import annotations

import asyncio

from fastmcp import FastMCP

from sentinel.mcp_server import create_server

EXPECTED_TOOLS = frozenset({
    "sentinel_check",
    "sentinel_alerts",
})


class TestSentinelMCPServer:
    def test_create_server_returns_fastmcp(self) -> None:
        server = create_server()
        assert isinstance(server, FastMCP)

    def test_server_has_expected_tools(self) -> None:
        server = create_server()
        tools = asyncio.run(server.list_tools())
        tool_names = {t.name for t in tools}
        assert tool_names == EXPECTED_TOOLS

    def test_tool_count(self) -> None:
        server = create_server()
        tools = asyncio.run(server.list_tools())
        assert len(tools) == 2
