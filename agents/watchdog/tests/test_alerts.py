"""Tests for watchdog alert persistence (WatchdogAlert + alerts_from_health)."""

from __future__ import annotations

import json

from shared.notify import append_to_log, read_log_lines

from watchdog.models import (
    AlertSeverity,
    CheckResult,
    RepoHealth,
    Status,
    WatchdogAlert,
)
from watchdog.scanner import alerts_from_health


def _health(checks: list[CheckResult]) -> RepoHealth:
    return RepoHealth(repo="owner/repo", checks=checks)


def test_all_pass_produces_no_alerts():
    health = _health([CheckResult(check_name="ci", status=Status.PASS, message="OK")])
    assert alerts_from_health(health) == []


def test_fail_produces_high_severity():
    health = _health([CheckResult(check_name="ci", status=Status.FAIL, message="CI red")])
    alerts = alerts_from_health(health)
    assert len(alerts) == 1
    assert alerts[0].severity == AlertSeverity.HIGH
    assert alerts[0].check_name == "ci"
    assert alerts[0].repo == "owner/repo"


def test_warn_produces_medium_severity():
    health = _health(
        [CheckResult(check_name="stale_prs", status=Status.WARN, message="3 stale PRs")]
    )
    alerts = alerts_from_health(health)
    assert len(alerts) == 1
    assert alerts[0].severity == AlertSeverity.MEDIUM


def test_mixed_checks():
    health = _health(
        [
            CheckResult(check_name="ci", status=Status.PASS, message="OK"),
            CheckResult(check_name="stale_prs", status=Status.WARN, message="stale"),
            CheckResult(check_name="security", status=Status.FAIL, message="vuln found"),
        ]
    )
    alerts = alerts_from_health(health)
    assert len(alerts) == 2
    severities = {a.severity for a in alerts}
    assert severities == {AlertSeverity.HIGH, AlertSeverity.MEDIUM}


def test_watchdog_alert_model_roundtrip():
    alert = WatchdogAlert(
        repo="owner/repo",
        check_name="ci",
        status=Status.FAIL,
        severity=AlertSeverity.HIGH,
        message="CI failing",
    )
    data = json.loads(alert.model_dump_json())
    assert data["repo"] == "owner/repo"
    assert data["severity"] == "high"
    assert data["status"] == "fail"
    restored = WatchdogAlert.model_validate(data)
    assert restored.check_name == "ci"


def test_jsonl_roundtrip(tmp_path):
    log = tmp_path / "alerts.jsonl"
    alert = WatchdogAlert(
        repo="owner/repo",
        check_name="stale_prs",
        status=Status.WARN,
        severity=AlertSeverity.MEDIUM,
        message="3 stale PRs",
    )
    append_to_log([alert], log)
    lines = read_log_lines(log)
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["check_name"] == "stale_prs"


def test_details_preserved():
    health = _health(
        [
            CheckResult(
                check_name="security",
                status=Status.FAIL,
                message="1 advisory",
                details="CVE-2026-1234: critical",
            )
        ]
    )
    alerts = alerts_from_health(health)
    assert alerts[0].details == "CVE-2026-1234: critical"


def test_empty_health_produces_no_alerts():
    health = _health([])
    assert alerts_from_health(health) == []
