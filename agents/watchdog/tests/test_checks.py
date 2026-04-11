"""Tests for watchdog checks -- tests CheckResult construction and report formatting.

These tests exercise the pure logic paths (result construction, status
aggregation, report formatting) without calling subprocess / gh.
"""

from __future__ import annotations

from watchdog.models import CheckResult, RepoHealth, Status
from watchdog.scanner import format_report


def _make_health(repo: str, checks: list[CheckResult]) -> RepoHealth:
    return RepoHealth(repo=repo, checks=checks)


def test_format_report_single_passing_repo():
    health = _make_health(
        "owner/repo",
        [
            CheckResult(check_name="stale_prs", status=Status.PASS, message="No stale PRs"),
            CheckResult(check_name="ci_status", status=Status.PASS, message="All CI passed"),
        ],
    )
    report = format_report([health])
    assert "# Watchdog Health Report" in report
    assert "owner/repo -- PASS" in report
    assert "[+] **stale_prs**" in report
    assert "[+] **ci_status**" in report
    assert "1 repo(s) scanned -- 1 pass, 0 warn, 0 fail" in report


def test_format_report_failing_repo():
    health = _make_health(
        "owner/repo",
        [
            CheckResult(
                check_name="ci_status",
                status=Status.FAIL,
                message="2/5 CI runs failed",
                details="  build on main (run 123)\n  test on main (run 124)",
            ),
        ],
    )
    report = format_report([health])
    assert "owner/repo -- FAIL" in report
    assert "[-] **ci_status**" in report
    assert "build on main" in report
    assert "1 repo(s) scanned -- 0 pass, 0 warn, 1 fail" in report


def test_format_report_warn_repo():
    health = _make_health(
        "owner/repo",
        [
            CheckResult(check_name="stale_prs", status=Status.WARN, message="3 stale PRs"),
        ],
    )
    report = format_report([health])
    assert "owner/repo -- WARN" in report
    assert "[~] **stale_prs**" in report


def test_format_report_multiple_repos():
    r1 = _make_health(
        "owner/a",
        [CheckResult(check_name="ci", status=Status.PASS, message="ok")],
    )
    r2 = _make_health(
        "owner/b",
        [CheckResult(check_name="ci", status=Status.FAIL, message="fail")],
    )
    report = format_report([r1, r2])
    assert "owner/a -- PASS" in report
    assert "owner/b -- FAIL" in report
    assert "2 repo(s) scanned -- 1 pass, 0 warn, 1 fail" in report


def test_format_report_no_checks():
    health = _make_health("owner/repo", [])
    report = format_report([health])
    assert "No checks ran." in report


def test_check_result_details_appear_in_report():
    health = _make_health(
        "owner/repo",
        [
            CheckResult(
                check_name="lockfile_audit",
                status=Status.FAIL,
                message="package-lock.json: vulnerabilities found",
                details="high: prototype-pollution in lodash\nmoderate: regex-dos in minimatch",
            ),
        ],
    )
    report = format_report([health])
    assert "prototype-pollution" in report
    assert "regex-dos" in report
