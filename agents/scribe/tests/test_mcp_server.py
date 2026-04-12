"""Tests for scribe MCP server."""

from __future__ import annotations

import asyncio

import pytest
from fastmcp import FastMCP

from scribe.mcp_server import create_server

EXPECTED_TOOLS = frozenset({"scribe_status", "scribe_stats", "scribe_recent"})


@pytest.fixture()
def server() -> FastMCP:
    return create_server()


class TestScribeMCPServer:
    def test_create_server_returns_fastmcp(self, server: FastMCP) -> None:
        assert isinstance(server, FastMCP)

    def test_server_has_expected_tools(self, server: FastMCP) -> None:
        tools = asyncio.run(server.list_tools())
        tool_names = {t.name for t in tools}
        assert tool_names == EXPECTED_TOOLS

    def test_tool_count(self, server: FastMCP) -> None:
        tools = asyncio.run(server.list_tools())
        assert len(tools) == 3
