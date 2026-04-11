"""Tests for the recall MCP server factory."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from fastmcp import FastMCP

from recall.mcp_server import create_server

EXPECTED_TOOLS = frozenset({
    "recall_add",
    "recall_search",
    "recall_list",
    "recall_get",
    "recall_delete",
    "recall_stats",
    "recall_extract",
    "recall_stale",
})


@pytest.fixture()
def server(tmp_path: Path) -> FastMCP:
    return create_server(db_path=tmp_path / "test.db")


class TestRecallMCPServer:
    def test_create_server_returns_fastmcp(self, server: FastMCP) -> None:
        assert isinstance(server, FastMCP)

    def test_server_has_expected_tools(self, server: FastMCP) -> None:
        tools = asyncio.run(server.list_tools())
        tool_names = {t.name for t in tools}
        assert tool_names == EXPECTED_TOOLS

    def test_tool_count(self, server: FastMCP) -> None:
        tools = asyncio.run(server.list_tools())
        assert len(tools) == 8
