"""FastMCP server for scribe."""

from __future__ import annotations

import json
from pathlib import Path

from fastmcp import FastMCP

from scribe.watcher import ACTIVITY_LOG, load_state


def create_server(db_path: Path | None = None) -> FastMCP:
    """Create the scribe MCP server."""
    mcp = FastMCP(
        "scribe",
        instructions=(
            "Session insight extractor. Watches Claude Code sessions and extracts "
            "structured insights into the recall knowledge store. Use scribe_status "
            "to check watch state, scribe_stats for activity statistics, and "
            "scribe_recent for recently generated insights."
        ),
    )

    @mcp.tool()
    def scribe_status() -> str:
        """Check the current scribe watch state."""
        state = load_state()
        tracked = len(state.sessions_tracked)
        analyzed = len(state.sessions_analyzed)
        pending = tracked - analyzed

        lines = [
            f"Sessions tracked: {tracked}",
            f"Sessions analyzed: {analyzed}",
            f"Pending analysis: {pending}",
        ]

        if state.last_poll_ts > 0:
            from datetime import datetime, timezone

            dt = datetime.fromtimestamp(state.last_poll_ts, tz=timezone.utc)
            lines.append(f"Last poll: {dt.isoformat()}")

        return "\n".join(lines)

    @mcp.tool()
    def scribe_stats(days: int = 30, project: str | None = None) -> str:
        """Get scribe activity statistics."""
        if not ACTIVITY_LOG.exists():
            return "No activity log found. Run 'scribe watch' first."

        entries = []
        for line in ACTIVITY_LOG.read_text().strip().splitlines():
            try:
                entries.append(json.loads(line))
            except (json.JSONDecodeError, ValueError):
                continue

        if project:
            entries = [e for e in entries if e.get("project") == project]

        total_sessions = len(entries)
        total_generated = sum(e.get("insights_generated", 0) for e in entries)
        total_added = sum(e.get("insights_added", 0) for e in entries)
        total_deduped = sum(e.get("insights_deduplicated", 0) for e in entries)

        return (
            f"Sessions analyzed: {total_sessions}\n"
            f"Insights generated: {total_generated}\n"
            f"Insights added to recall: {total_added}\n"
            f"Insights deduplicated: {total_deduped}"
        )

    @mcp.tool()
    def scribe_recent(limit: int = 10) -> str:
        """Get recent scribe activity entries."""
        if not ACTIVITY_LOG.exists():
            return "No activity log found."

        lines = ACTIVITY_LOG.read_text().strip().splitlines()
        recent = []
        for line in reversed(lines):
            try:
                entry = json.loads(line)
                sid = entry.get("session_id", "?")[:12]
                proj = entry.get("project", "-")
                added = entry.get("insights_added", 0)
                ts = entry.get("timestamp", "")[:19]
                recent.append(f"[{ts}] {sid} ({proj}): +{added} insights")
            except (json.JSONDecodeError, ValueError):
                continue
            if len(recent) >= limit:
                break

        return "\n".join(recent) if recent else "No recent activity."

    return mcp
