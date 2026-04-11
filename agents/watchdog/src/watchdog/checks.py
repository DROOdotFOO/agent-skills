"""Individual health check functions.

Each check returns a list of CheckResult. All GitHub API calls go through
the `gh` CLI via subprocess. Missing tools produce a warn result rather
than crashing.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from watchdog.models import CheckResult, Status


def _run_gh(args: list[str], repo: str | None = None) -> subprocess.CompletedProcess[str]:
    """Run a gh CLI command. Raises FileNotFoundError if gh is missing."""
    cmd = ["gh"]
    if repo:
        cmd.extend(["-R", repo])
    cmd.extend(args)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30)


def _gh_available() -> bool:
    return shutil.which("gh") is not None


def _missing_tool_result(check_name: str, tool: str) -> list[CheckResult]:
    return [
        CheckResult(
            check_name=check_name,
            status=Status.WARN,
            message=f"{tool} not found in PATH",
            details=f"Install {tool} to enable this check.",
        )
    ]


def check_stale_prs(repo: str, max_age_days: int = 14) -> list[CheckResult]:
    """Find PRs older than max_age_days."""
    if not _gh_available():
        return _missing_tool_result("stale_prs", "gh")

    result = _run_gh(
        [
            "pr",
            "list",
            "--state",
            "open",
            "--json",
            "number,title,createdAt,author",
            "--limit",
            "50",
        ],
        repo=repo,
    )
    if result.returncode != 0:
        return [
            CheckResult(
                check_name="stale_prs",
                status=Status.WARN,
                message=f"Failed to list PRs: {result.stderr.strip()}",
            )
        ]

    prs = json.loads(result.stdout) if result.stdout.strip() else []
    now = datetime.now(timezone.utc)
    results: list[CheckResult] = []

    stale_prs = []
    for pr in prs:
        created = datetime.fromisoformat(pr["createdAt"].replace("Z", "+00:00"))
        age_days = (now - created).days
        if age_days >= max_age_days:
            author = pr.get("author", {}).get("login", "unknown")
            stale_prs.append(f"  #{pr['number']} ({age_days}d) by {author}: {pr['title']}")

    if stale_prs:
        results.append(
            CheckResult(
                check_name="stale_prs",
                status=Status.WARN,
                message=f"{len(stale_prs)} PR(s) older than {max_age_days} days",
                details="\n".join(stale_prs),
            )
        )
    else:
        results.append(
            CheckResult(
                check_name="stale_prs",
                status=Status.PASS,
                message=f"No PRs older than {max_age_days} days",
            )
        )

    return results


def check_ci_status(repo: str) -> list[CheckResult]:
    """Check recent CI workflow runs for failures."""
    if not _gh_available():
        return _missing_tool_result("ci_status", "gh")

    result = _run_gh(
        [
            "run",
            "list",
            "--limit",
            "5",
            "--json",
            "databaseId,name,conclusion,createdAt,headBranch",
        ],
        repo=repo,
    )
    if result.returncode != 0:
        return [
            CheckResult(
                check_name="ci_status",
                status=Status.WARN,
                message=f"Failed to list CI runs: {result.stderr.strip()}",
            )
        ]

    runs = json.loads(result.stdout) if result.stdout.strip() else []
    if not runs:
        return [
            CheckResult(
                check_name="ci_status",
                status=Status.PASS,
                message="No CI runs found",
            )
        ]

    failures = []
    for run in runs:
        if run.get("conclusion") == "failure":
            branch = run.get("headBranch", "?")
            name = run.get("name", "?")
            failures.append(f"  {name} on {branch} (run {run.get('databaseId', '?')})")

    if failures:
        return [
            CheckResult(
                check_name="ci_status",
                status=Status.FAIL,
                message=f"{len(failures)}/{len(runs)} recent CI runs failed",
                details="\n".join(failures),
            )
        ]

    return [
        CheckResult(
            check_name="ci_status",
            status=Status.PASS,
            message=f"All {len(runs)} recent CI runs passed",
        )
    ]


def check_open_issues_age(repo: str, max_age_days: int = 30) -> list[CheckResult]:
    """Find assigned issues older than max_age_days."""
    if not _gh_available():
        return _missing_tool_result("open_issues_age", "gh")

    result = _run_gh(
        [
            "issue",
            "list",
            "--state",
            "open",
            "--json",
            "number,title,createdAt,assignees",
            "--limit",
            "50",
        ],
        repo=repo,
    )
    if result.returncode != 0:
        return [
            CheckResult(
                check_name="open_issues_age",
                status=Status.WARN,
                message=f"Failed to list issues: {result.stderr.strip()}",
            )
        ]

    issues = json.loads(result.stdout) if result.stdout.strip() else []
    now = datetime.now(timezone.utc)
    stale = []

    for issue in issues:
        assignees = issue.get("assignees", [])
        if not assignees:
            continue
        created = datetime.fromisoformat(issue["createdAt"].replace("Z", "+00:00"))
        age_days = (now - created).days
        if age_days >= max_age_days:
            names = ", ".join(a.get("login", "?") for a in assignees)
            stale.append(
                f"  #{issue['number']} ({age_days}d) assigned to {names}: {issue['title']}"
            )

    if stale:
        return [
            CheckResult(
                check_name="open_issues_age",
                status=Status.WARN,
                message=f"{len(stale)} assigned issue(s) older than {max_age_days} days",
                details="\n".join(stale),
            )
        ]

    return [
        CheckResult(
            check_name="open_issues_age",
            status=Status.PASS,
            message=f"No stale assigned issues (>{max_age_days} days)",
        )
    ]


_TODO_ISSUE_RE = re.compile(
    r"#\s*TODO.*?#(\d+)|#\s*FIXME.*?#(\d+)|TODO.*?#(\d+)|FIXME.*?#(\d+)",
    re.IGNORECASE,
)


def check_todo_closed_refs(repo_path: str) -> list[CheckResult]:
    """Grep for TODOs referencing issue numbers, check if those issues are closed."""
    path = Path(repo_path)
    if not path.is_dir():
        return [
            CheckResult(
                check_name="todo_closed_refs",
                status=Status.WARN,
                message=f"Repo path not found: {repo_path}",
            )
        ]

    if not _gh_available():
        return _missing_tool_result("todo_closed_refs", "gh")

    # Use grep to find TODO/FIXME lines with issue refs
    try:
        grep_result = subprocess.run(
            ["grep", "-rn", "-E", r"(TODO|FIXME).*#[0-9]+", "."],
            capture_output=True,
            text=True,
            cwd=repo_path,
            timeout=15,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return [
            CheckResult(
                check_name="todo_closed_refs",
                status=Status.WARN,
                message="grep failed or timed out",
            )
        ]

    if grep_result.returncode != 0:
        return [
            CheckResult(
                check_name="todo_closed_refs",
                status=Status.PASS,
                message="No TODO/FIXME issue references found",
            )
        ]

    # Extract unique issue numbers
    issue_numbers: set[int] = set()
    lines = grep_result.stdout.strip().splitlines()
    for line in lines:
        for match in re.finditer(r"#(\d+)", line):
            num = int(match.group(1))
            if num > 0:
                issue_numbers.add(num)

    if not issue_numbers:
        return [
            CheckResult(
                check_name="todo_closed_refs",
                status=Status.PASS,
                message="No TODO/FIXME issue references found",
            )
        ]

    # Detect repo name from git remote
    remote_result = subprocess.run(
        ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
        capture_output=True,
        text=True,
        cwd=repo_path,
        timeout=10,
    )
    if remote_result.returncode != 0 or not remote_result.stdout.strip():
        return [
            CheckResult(
                check_name="todo_closed_refs",
                status=Status.WARN,
                message="Could not determine repo name from git remote",
            )
        ]

    repo_name = remote_result.stdout.strip()
    closed_refs: list[str] = []

    for num in sorted(issue_numbers):
        issue_result = _run_gh(
            ["issue", "view", str(num), "--json", "state", "-q", ".state"],
            repo=repo_name,
        )
        if issue_result.returncode == 0 and issue_result.stdout.strip() == "CLOSED":
            # Find which TODO lines reference this issue
            ref_lines = [line for line in lines if f"#{num}" in line]
            for ref in ref_lines[:3]:  # limit detail noise
                closed_refs.append(f"  #{num} (CLOSED): {ref.strip()[:120]}")

    if closed_refs:
        return [
            CheckResult(
                check_name="todo_closed_refs",
                status=Status.WARN,
                message=f"{len(closed_refs)} TODO(s) reference closed issues",
                details="\n".join(closed_refs),
            )
        ]

    return [
        CheckResult(
            check_name="todo_closed_refs",
            status=Status.PASS,
            message=f"Checked {len(issue_numbers)} issue refs, none are closed",
        )
    ]


_LOCKFILE_AUDITORS: dict[str, list[list[str]]] = {
    "package-lock.json": [["npm", "audit", "--json"]],
    "yarn.lock": [["yarn", "audit", "--json"]],
    "pnpm-lock.yaml": [["pnpm", "audit", "--json"]],
    "Cargo.lock": [["cargo", "audit", "--json"]],
    "requirements.txt": [["pip-audit", "--format", "json"]],
    "Pipfile.lock": [["pip-audit", "--format", "json"]],
    "poetry.lock": [["pip-audit", "--format", "json"]],
    "mix.lock": [["mix", "deps.audit"]],
}


def check_lockfile_audit(repo_path: str) -> list[CheckResult]:
    """Detect lockfile type and run the appropriate audit tool."""
    path = Path(repo_path)
    if not path.is_dir():
        return [
            CheckResult(
                check_name="lockfile_audit",
                status=Status.WARN,
                message=f"Repo path not found: {repo_path}",
            )
        ]

    results: list[CheckResult] = []
    found_lockfile = False

    for lockfile, audit_cmds in _LOCKFILE_AUDITORS.items():
        if not (path / lockfile).exists():
            continue
        found_lockfile = True

        for cmd in audit_cmds:
            tool = cmd[0]
            if not shutil.which(tool):
                results.append(
                    CheckResult(
                        check_name="lockfile_audit",
                        status=Status.WARN,
                        message=f"{tool} not found, cannot audit {lockfile}",
                    )
                )
                continue

            try:
                audit_result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=repo_path,
                    timeout=60,
                )
            except subprocess.TimeoutExpired:
                results.append(
                    CheckResult(
                        check_name="lockfile_audit",
                        status=Status.WARN,
                        message=f"{tool} audit timed out for {lockfile}",
                    )
                )
                continue

            if audit_result.returncode == 0:
                results.append(
                    CheckResult(
                        check_name="lockfile_audit",
                        status=Status.PASS,
                        message=f"{lockfile}: no vulnerabilities found",
                    )
                )
            else:
                # Most audit tools return non-zero when vulns are found
                detail = (
                    audit_result.stdout[:500] if audit_result.stdout else audit_result.stderr[:500]
                )
                results.append(
                    CheckResult(
                        check_name="lockfile_audit",
                        status=Status.FAIL,
                        message=f"{lockfile}: vulnerabilities found",
                        details=detail.strip(),
                    )
                )

    if not found_lockfile:
        results.append(
            CheckResult(
                check_name="lockfile_audit",
                status=Status.PASS,
                message="No recognized lockfile found",
            )
        )

    return results


def check_security_advisories(repo: str) -> list[CheckResult]:
    """Check for Dependabot / vulnerability alerts via gh API."""
    if not _gh_available():
        return _missing_tool_result("security_advisories", "gh")

    result = _run_gh(
        ["api", f"repos/{repo}/dependabot/alerts", "--jq", "length"],
        repo=None,
    )

    if result.returncode != 0:
        stderr = result.stderr.strip()
        if "Dependabot alerts are not enabled" in stderr or "not enabled" in stderr.lower():
            return [
                CheckResult(
                    check_name="security_advisories",
                    status=Status.PASS,
                    message="Dependabot alerts not enabled for this repo",
                )
            ]
        if "404" in stderr or "Not Found" in stderr:
            return [
                CheckResult(
                    check_name="security_advisories",
                    status=Status.WARN,
                    message="Cannot access vulnerability alerts (check permissions)",
                )
            ]
        return [
            CheckResult(
                check_name="security_advisories",
                status=Status.WARN,
                message=f"Failed to check advisories: {stderr[:200]}",
            )
        ]

    count_str = result.stdout.strip()
    try:
        count = int(count_str)
    except ValueError:
        # Response might be the full JSON array; try parsing
        try:
            alerts = json.loads(result.stdout)
            count = len(alerts) if isinstance(alerts, list) else 0
        except (json.JSONDecodeError, TypeError):
            return [
                CheckResult(
                    check_name="security_advisories",
                    status=Status.WARN,
                    message="Unexpected response from dependabot API",
                )
            ]

    if count > 0:
        return [
            CheckResult(
                check_name="security_advisories",
                status=Status.FAIL,
                message=f"{count} open Dependabot alert(s)",
            )
        ]

    return [
        CheckResult(
            check_name="security_advisories",
            status=Status.PASS,
            message="No open Dependabot alerts",
        )
    ]
