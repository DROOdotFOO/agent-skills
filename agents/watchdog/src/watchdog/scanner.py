"""Orchestrates health checks across repos and formats reports."""

from __future__ import annotations

from datetime import datetime

from watchdog.checks import (
    check_ci_status,
    check_lockfile_audit,
    check_open_issues_age,
    check_security_advisories,
    check_stale_prs,
    check_todo_closed_refs,
)
from watchdog.models import AlertSeverity, RepoHealth, Status, WatchConfig, WatchdogAlert


def scan_repo(
    repo: str,
    repo_path: str | None = None,
    stale_pr_days: int = 14,
    stale_issue_days: int = 30,
) -> RepoHealth:
    """Run all health checks for a single repo."""
    health = RepoHealth(repo=repo)

    # GitHub API checks (work with owner/repo string)
    health.checks.extend(check_stale_prs(repo, max_age_days=stale_pr_days))
    health.checks.extend(check_ci_status(repo))
    health.checks.extend(check_open_issues_age(repo, max_age_days=stale_issue_days))
    health.checks.extend(check_security_advisories(repo))

    # Local path checks (require a cloned repo on disk)
    if repo_path:
        health.checks.extend(check_todo_closed_refs(repo_path))
        health.checks.extend(check_lockfile_audit(repo_path))

    return health


def scan_all(config: WatchConfig) -> list[RepoHealth]:
    """Scan all repos in config."""
    results: list[RepoHealth] = []
    for repo_cfg in config.repos:
        health = scan_repo(
            repo=repo_cfg.name,
            repo_path=repo_cfg.path,
            stale_pr_days=config.thresholds.stale_pr_days,
            stale_issue_days=config.thresholds.stale_issue_days,
        )
        results.append(health)
    return results


def alerts_from_health(health: RepoHealth) -> list[WatchdogAlert]:
    """Convert WARN/FAIL check results to persistable WatchdogAlerts."""
    alerts: list[WatchdogAlert] = []
    for check in health.checks:
        if check.status == Status.FAIL:
            severity = AlertSeverity.HIGH
        elif check.status == Status.WARN:
            severity = AlertSeverity.MEDIUM
        else:
            continue
        alerts.append(
            WatchdogAlert(
                repo=health.repo,
                check_name=check.check_name,
                status=check.status,
                severity=severity,
                message=check.message,
                details=check.details,
            )
        )
    return alerts


def format_report(results: list[RepoHealth]) -> str:
    """Format scan results as a markdown report."""
    lines: list[str] = []
    now = datetime.now()
    lines.append("# Watchdog Health Report")
    lines.append("")
    lines.append(f"Generated: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    status_label = {
        Status.PASS: "PASS",
        Status.WARN: "WARN",
        Status.FAIL: "FAIL",
    }

    for health in results:
        overall = status_label[health.overall_status]
        lines.append(f"## {health.repo} -- {overall}")
        lines.append("")

        if not health.checks:
            lines.append("No checks ran.")
            lines.append("")
            continue

        for check in health.checks:
            prefix = {"pass": "[+]", "warn": "[~]", "fail": "[-]"}[check.status.value]
            lines.append(f"- {prefix} **{check.check_name}**: {check.message}")
            if check.details:
                for detail_line in check.details.splitlines():
                    lines.append(f"  {detail_line}")

        lines.append("")

    # Summary
    total = len(results)
    failing = sum(1 for r in results if r.overall_status == Status.FAIL)
    warning = sum(1 for r in results if r.overall_status == Status.WARN)
    passing = sum(1 for r in results if r.overall_status == Status.PASS)
    lines.append("---")
    lines.append(
        f"**Summary**: {total} repo(s) scanned -- {passing} pass, {warning} warn, {failing} fail"
    )
    lines.append("")

    return "\n".join(lines)
