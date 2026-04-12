"""Tests for the autoresearch MCP server factory."""

from __future__ import annotations

import asyncio
from pathlib import Path

from fastmcp import FastMCP

from autoresearch.mcp_server import create_server

EXPECTED_TOOLS = frozenset(
    {
        "autoresearch_status",
        "autoresearch_dashboard",
        "autoresearch_run",
    }
)


class TestAutoresearchMCPServer:
    def test_create_server_returns_fastmcp(self, tmp_path: Path) -> None:
        server = create_server(work_dir=tmp_path)
        assert isinstance(server, FastMCP)

    def test_server_has_expected_tools(self, tmp_path: Path) -> None:
        server = create_server(work_dir=tmp_path)
        tools = asyncio.run(server.list_tools())
        tool_names = {t.name for t in tools}
        assert tool_names == EXPECTED_TOOLS

    def test_tool_count(self, tmp_path: Path) -> None:
        server = create_server(work_dir=tmp_path)
        tools = asyncio.run(server.list_tools())
        assert len(tools) == 3
