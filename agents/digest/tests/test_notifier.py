"""Tests for the notification dispatcher."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from digest.alerts import AlertSeverity, DigestAlert
from digest.notifier import append_to_log, read_log


def _alert(
    topic: str = "test",
    severity: AlertSeverity = AlertSeverity.MEDIUM,
    rule: str = "test_rule",
    message: str = "test message",
) -> DigestAlert:
    return DigestAlert(
        topic=topic,
        severity=severity,
        rule=rule,
        message=message,
        items=["https://example.com"],
        timestamp=datetime(2026, 4, 12, 12, 0, 0, tzinfo=timezone.utc),
    )


class TestAlertLog:
    def test_append_creates_file(self, tmp_path: Path) -> None:
        log_path = tmp_path / "alerts.jsonl"
        append_to_log([_alert()], log_path)
        assert log_path.exists()
        lines = log_path.read_text().strip().splitlines()
        assert len(lines) == 1

    def test_append_multiple_alerts(self, tmp_path: Path) -> None:
        log_path = tmp_path / "alerts.jsonl"
        append_to_log([_alert(), _alert(topic="other")], log_path)
        lines = log_path.read_text().strip().splitlines()
        assert len(lines) == 2

    def test_append_is_additive(self, tmp_path: Path) -> None:
        log_path = tmp_path / "alerts.jsonl"
        append_to_log([_alert()], log_path)
        append_to_log([_alert(topic="second")], log_path)
        lines = log_path.read_text().strip().splitlines()
        assert len(lines) == 2

    def test_read_empty_when_no_file(self, tmp_path: Path) -> None:
        log_path = tmp_path / "nonexistent.jsonl"
        alerts = read_log(log_path)
        assert alerts == []

    def test_read_roundtrips(self, tmp_path: Path) -> None:
        log_path = tmp_path / "alerts.jsonl"
        original = _alert(topic="roundtrip", message="hello")
        append_to_log([original], log_path)
        loaded = read_log(log_path)
        assert len(loaded) == 1
        assert loaded[0].topic == "roundtrip"
        assert loaded[0].message == "hello"

    def test_read_newest_first(self, tmp_path: Path) -> None:
        log_path = tmp_path / "alerts.jsonl"
        append_to_log([_alert(topic="first")], log_path)
        append_to_log([_alert(topic="second")], log_path)
        loaded = read_log(log_path)
        assert loaded[0].topic == "second"
        assert loaded[1].topic == "first"

    def test_read_respects_limit(self, tmp_path: Path) -> None:
        log_path = tmp_path / "alerts.jsonl"
        for i in range(10):
            append_to_log([_alert(topic=f"t{i}")], log_path)
        loaded = read_log(log_path, limit=3)
        assert len(loaded) == 3
        # Should get the 3 most recent
        assert loaded[0].topic == "t9"

    def test_read_skips_corrupt_lines(self, tmp_path: Path) -> None:
        log_path = tmp_path / "alerts.jsonl"
        append_to_log([_alert()], log_path)
        with log_path.open("a") as f:
            f.write("not valid json\n")
        append_to_log([_alert(topic="after_corrupt")], log_path)
        loaded = read_log(log_path)
        assert len(loaded) == 2
        assert loaded[0].topic == "after_corrupt"
