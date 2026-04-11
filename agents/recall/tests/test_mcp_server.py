"""Tests for the recall MCP server tool functions."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from recall.mcp_server import create_server


@pytest.fixture()
def server(tmp_path: Path):
    return create_server(db_path=tmp_path / "test.db")


class TestMCPTools:
    def test_server_has_expected_tools(self, server):
        tools = asyncio.run(server.list_tools())
        tool_names = [t.name for t in tools]
        assert "recall_add" in tool_names
        assert "recall_search" in tool_names
        assert "recall_list" in tool_names
        assert "recall_get" in tool_names
        assert "recall_delete" in tool_names
        assert "recall_stats" in tool_names
        assert "recall_stale" in tool_names
        assert "recall_extract" in tool_names

    def test_tool_count(self, server):
        tools = asyncio.run(server.list_tools())
        assert len(tools) == 8
