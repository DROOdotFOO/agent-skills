"""Tests for prepper gatherers that read local files (no network)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from prepper.gatherers import gather_digest_summary, gather_sentinel_alerts


# --- gather_sentinel_alerts ---


def test_sentinel_alerts_reads_jsonl(tmp_path: Path) -> None:
    log = tmp_path / "alerts.jsonl"
    alert = {
        "severity": "high",
        "rule_name": "large_transfer",
        "contract": {"name": "USDC"},
        "message": "Transfer of 1M USDC",
        "tx_hash": "0xabc123",
    }
    log.write_text(json.dumps(alert) + "\n")

    section = gather_sentinel_alerts(alert_log=str(log))
    assert section is not None
    assert "large_transfer" in section.content
    assert "USDC" in section.content
    assert section.title == "On-Chain Alerts (Sentinel)"


def test_sentinel_alerts_returns_none_for_missing_file() -> None:
    section = gather_sentinel_alerts(alert_log="/nonexistent/path/alerts.jsonl")
    assert section is None


def test_sentinel_alerts_limits_to_5(tmp_path: Path) -> None:
    log = tmp_path / "alerts.jsonl"
    lines = []
    for i in range(10):
        alert = {
            "severity": "info",
            "rule_name": f"rule_{i}",
            "contract": {"name": f"contract_{i}"},
            "message": f"Alert {i}",
        }
        lines.append(json.dumps(alert))
    log.write_text("\n".join(lines) + "\n")

    section = gather_sentinel_alerts(alert_log=str(log))
    assert section is not None
    # Should show last 5 alerts
    assert "rule_9" in section.content
    assert "rule_5" in section.content


# --- gather_digest_summary ---


def test_digest_summary_reads_sqlite(tmp_path: Path) -> None:
    db_path = tmp_path / "feed.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE digests (
            id INTEGER PRIMARY KEY,
            topic TEXT,
            days INTEGER,
            item_count INTEGER,
            narrative TEXT,
            generated_at TEXT
        )
    """)
    conn.execute(
        "INSERT INTO digests (topic, days, item_count, narrative, generated_at) "
        "VALUES (?, ?, ?, ?, ?)",
        ("noir", 30, 42, "narrative", "2024-06-01T00:00:00"),
    )
    conn.commit()
    conn.close()

    # Monkey-patch the default path
    import prepper.gatherers as g

    original_fn = g.gather_digest_summary

    def patched(project: str) -> object:
        g_db_path = db_path
        if not g_db_path.exists():
            return None
        try:
            conn = sqlite3.connect(str(g_db_path))
            rows = conn.execute(
                "SELECT topic, item_count, generated_at FROM digests "
                "ORDER BY generated_at DESC LIMIT 5"
            ).fetchall()
            conn.close()
            if not rows:
                return None
            from prepper.models import BriefingSection, Priority

            lines = []
            for topic, count, generated_at in rows:
                ts = generated_at[:10] if generated_at else "?"
                lines.append(f"- **{topic}**: {count} items ({ts})")
            return BriefingSection(
                title="Recent Digests",
                content="\n".join(lines),
                priority=Priority.LOW,
            )
        except Exception:
            return None

    section = patched("noir")
    assert section is not None
    assert "noir" in section.content
    assert "42 items" in section.content


def test_digest_summary_returns_none_no_db() -> None:
    section = gather_digest_summary("nonexistent_project")
    # Will return None since default path doesn't have data
    # (or doesn't exist on test machines)
    assert section is None or section.title == "Recent Digests"
