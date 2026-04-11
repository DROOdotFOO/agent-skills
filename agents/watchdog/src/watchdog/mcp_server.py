"""FastMCP server exposing watchdog tools for Claude Code integration."""

from __future__ import annotations

from fastmcp import FastMCP

from watchdog.models import RepoConfig, WatchConfig
from watchdog.scanner import format_report, scan_all, scan_repo


def create_server() -> FastMCP:
    """Create a FastMCP server with watchdog tools."""
    mcp = FastMCP(
        "watchdog",
        instructions=(
            "Continuous repo health monitor. Use watchdog_scan to check repo health "
            "(stale PRs, CI status, issue age, TODO refs, lockfile audit, security advisories). "
            "Accepts GitHub repos as owner/repo strings."
        ),
    )

    @mcp.tool()
    def watchdog_scan(
        repos: str,
        stale_pr_days: int = 14,
        stale_issue_days: int = 30,
    ) -> str:
        """Scan one or more repos for health issues.

        Args:
            repos: Comma-separated repo identifiers (e.g. "owner/repo,owner2/repo2")
            stale_pr_days: PRs older than this are flagged as stale (default 14)
            stale_issue_days: Issues older than this are flagged (default 30)
        """
        repo_list = [r.strip() for r in repos.split(",") if r.strip()]
        if not repo_list:
            return "No repos specified."

        config = WatchConfig(
            repos=[RepoConfig(name=r) for r in repo_list],
        )
        config.thresholds.stale_pr_days = stale_pr_days
        config.thresholds.stale_issue_days = stale_issue_days

        results = scan_all(config)
        return format_report(results)

    @mcp.tool()
    def watchdog_scan_local(
        repo: str,
        path: str,
        stale_pr_days: int = 14,
        stale_issue_days: int = 30,
    ) -> str:
        """Scan a repo with a local path for additional checks (TODO refs, lockfile audit).

        Args:
            repo: Repo identifier (e.g. "owner/repo")
            path: Local filesystem path to the cloned repo
            stale_pr_days: PRs older than this are flagged as stale (default 14)
            stale_issue_days: Issues older than this are flagged (default 30)
        """
        health = scan_repo(
            repo=repo,
            repo_path=path,
            stale_pr_days=stale_pr_days,
            stale_issue_days=stale_issue_days,
        )
        return format_report([health])

    return mcp
