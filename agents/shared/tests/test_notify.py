"""Tests for shared.notify."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from pydantic import BaseModel, Field

from shared.notify import append_to_log, notify_macos, read_log_lines


class _FakeAlert(BaseModel):
    severity: str
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def test_append_creates_file(tmp_path):
    log = tmp_path / "alerts.jsonl"
    alerts = [_FakeAlert(severity="high", message="test")]
    append_to_log(alerts, log)
    assert log.exists()
    lines = log.read_text().strip().splitlines()
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["severity"] == "high"
    assert data["message"] == "test"


def test_append_is_additive(tmp_path):
    log = tmp_path / "alerts.jsonl"
    append_to_log([_FakeAlert(severity="low", message="a")], log)
    append_to_log([_FakeAlert(severity="high", message="b")], log)
    lines = log.read_text().strip().splitlines()
    assert len(lines) == 2


def test_append_creates_parent_dirs(tmp_path):
    log = tmp_path / "nested" / "dir" / "alerts.jsonl"
    append_to_log([_FakeAlert(severity="info", message="deep")], log)
    assert log.exists()


def test_read_log_lines_missing_file(tmp_path):
    result = read_log_lines(tmp_path / "nonexistent.jsonl")
    assert result == []


def test_read_log_lines_newest_first(tmp_path):
    log = tmp_path / "alerts.jsonl"
    append_to_log([_FakeAlert(severity="low", message="first")], log)
    append_to_log([_FakeAlert(severity="high", message="second")], log)
    lines = read_log_lines(log)
    assert len(lines) == 2
    assert json.loads(lines[0])["message"] == "second"
    assert json.loads(lines[1])["message"] == "first"


def test_read_log_lines_respects_limit(tmp_path):
    log = tmp_path / "alerts.jsonl"
    for i in range(10):
        append_to_log([_FakeAlert(severity="info", message=f"msg-{i}")], log)
    lines = read_log_lines(log, limit=3)
    assert len(lines) == 3
    assert json.loads(lines[0])["message"] == "msg-9"


def test_read_log_lines_skips_empty_lines(tmp_path):
    log = tmp_path / "alerts.jsonl"
    log.write_text('{"severity":"high","message":"ok"}\n\n\n')
    lines = read_log_lines(log)
    assert len(lines) == 1


def test_notify_macos_noop_on_empty_title():
    # Should not raise even with empty strings
    notify_macos("", "", use_osascript=False)
