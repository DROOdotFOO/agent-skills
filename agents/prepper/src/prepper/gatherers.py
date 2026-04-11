"""Context gatherers. Each returns a BriefingSection or None."""

from __future__ import annotations

import subprocess
from pathlib import Path
from shutil import which

from prepper.models import BriefingSection, Priority


def _run(args: list[str], cwd: str | None = None, timeout: int = 30) -> str | None:
    """Run a subprocess and return stdout, or None on failure."""
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout,
        )
        if result.returncode != 0:
            return None
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None


def gather_git_activity(repo_path: str) -> BriefingSection | None:
    """Recent commits, active branches, and uncommitted changes."""
    if not which("git"):
        return None

    path = Path(repo_path)
    if not (path / ".git").exists():
        return None

    lines: list[str] = []

    # Recent commits (last 7 days)
    log = _run(
        ["git", "log", "--since=7 days ago", "--oneline", "--no-decorate", "-20"],
        cwd=repo_path,
    )
    if log:
        lines.append("### Recent commits (7d)")
        lines.append("")
        lines.append("```")
        lines.append(log)
        lines.append("```")
        lines.append("")

    # Active branches
    branches = _run(
        ["git", "branch", "--sort=-committerdate", "--format=%(refname:short)", "--no-merged"],
        cwd=repo_path,
    )
    if branches:
        branch_list = branches.splitlines()[:10]
        lines.append("### Active branches")
        lines.append("")
        for b in branch_list:
            lines.append(f"- {b}")
        lines.append("")

    # Current branch
    current = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_path)
    if current:
        lines.insert(0, f"**Current branch:** {current}")
        lines.insert(1, "")

    # Uncommitted changes
    status = _run(["git", "status", "--porcelain"], cwd=repo_path)
    if status:
        changed = len(status.splitlines())
        lines.append(f"### Uncommitted changes ({changed} files)")
        lines.append("")
        lines.append("```")
        lines.append(status)
        lines.append("```")

    if not lines:
        return None

    return BriefingSection(
        title="Git Activity",
        content="\n".join(lines),
        priority=Priority.HIGH,
    )


def gather_github_state(repo: str) -> BriefingSection | None:
    """Open PRs, assigned issues, and failing checks from GitHub."""
    if not which("gh"):
        return None

    lines: list[str] = []

    # Open PRs authored by me
    prs = _run(["gh", "pr", "list", "--author", "@me", "--repo", repo, "--limit", "10"])
    if prs:
        lines.append("### My open PRs")
        lines.append("")
        lines.append("```")
        lines.append(prs)
        lines.append("```")
        lines.append("")

    # Assigned issues
    issues = _run(["gh", "issue", "list", "--assignee", "@me", "--repo", repo, "--limit", "10"])
    if issues:
        lines.append("### Assigned issues")
        lines.append("")
        lines.append("```")
        lines.append(issues)
        lines.append("```")
        lines.append("")

    # Failing checks
    failures = _run(["gh", "run", "list", "--status", "failure", "--repo", repo, "--limit", "5"])
    if failures:
        lines.append("### Failing CI runs")
        lines.append("")
        lines.append("```")
        lines.append(failures)
        lines.append("```")

    if not lines:
        return None

    return BriefingSection(
        title="GitHub State",
        content="\n".join(lines),
        priority=Priority.HIGH,
    )


def gather_dependency_status(repo_path: str) -> BriefingSection | None:
    """Detect lockfile and report outdated or vulnerable dependencies."""
    path = Path(repo_path)
    lines: list[str] = []

    # npm/pnpm
    if (path / "package-lock.json").exists() or (path / "pnpm-lock.yaml").exists():
        audit = _run(["npm", "audit", "--json"], cwd=repo_path, timeout=60)
        if audit:
            lines.append("### npm audit")
            lines.append("")
            # Just report that audit ran; full JSON is too verbose
            lines.append("npm audit completed. Check output for details.")
            lines.append("")

        outdated = _run(["npm", "outdated"], cwd=repo_path, timeout=60)
        if outdated:
            lines.append("### Outdated npm packages")
            lines.append("")
            lines.append("```")
            lines.append(outdated)
            lines.append("```")
            lines.append("")

    # Python
    has_python = (path / "pyproject.toml").exists() or (path / "requirements.txt").exists()
    if has_python and which("pip"):
        outdated = _run(
            ["pip", "list", "--outdated", "--format=columns"],
            cwd=repo_path,
            timeout=60,
        )
        if outdated:
            lines.append("### Outdated Python packages")
            lines.append("")
            lines.append("```")
            lines.append(outdated)
            lines.append("```")
            lines.append("")

    # Mix (Elixir)
    if (path / "mix.lock").exists() and which("mix"):
        outdated = _run(["mix", "hex.outdated"], cwd=repo_path, timeout=60)
        if outdated:
            lines.append("### Outdated Hex packages")
            lines.append("")
            lines.append("```")
            lines.append(outdated)
            lines.append("```")

    # Go
    if (path / "go.sum").exists() and which("go"):
        outdated = _run(
            ["go", "list", "-m", "-u", "all"],
            cwd=repo_path,
            timeout=60,
        )
        if outdated:
            lines.append("### Go module updates")
            lines.append("")
            lines.append("```")
            lines.append(outdated)
            lines.append("```")

    if not lines:
        return None

    return BriefingSection(
        title="Dependency Status",
        content="\n".join(lines),
        priority=Priority.LOW,
    )


def gather_recall_context(project: str) -> BriefingSection | None:
    """Search recall store for recent entries about this project."""
    try:
        from recall.store import RecallStore
    except ImportError:
        return None

    try:
        store = RecallStore()
        entries = store.search(project, project=project, limit=10)
        if not entries:
            return None

        lines: list[str] = []
        for entry in entries:
            entry_type = getattr(entry, "entry_type", "insight")
            lines.append(f"- **[{entry_type}]** {entry.content[:120]}")

        return BriefingSection(
            title="Recall Context",
            content="\n".join(lines),
            priority=Priority.MEDIUM,
        )
    except Exception:
        return None


def gather_sentinel_alerts(alert_log: str = "alerts.jsonl") -> BriefingSection | None:
    """Surface recent on-chain alerts from sentinel's log."""
    alerts_path = Path(alert_log)
    if not alerts_path.exists():
        # Check default location
        alerts_path = Path.home() / ".local" / "share" / "sentinel" / "alerts.jsonl"
        if not alerts_path.exists():
            return None

    try:
        import json

        lines_raw = alerts_path.read_text().strip().splitlines()
        recent = lines_raw[-5:]  # Last 5 alerts
        if not recent:
            return None

        lines: list[str] = []
        for raw_line in reversed(recent):
            data = json.loads(raw_line)
            severity = data.get("severity", "").upper()
            rule = data.get("rule_name", "")
            contract = data.get("contract", {}).get("name", "")
            message = data.get("message", "")
            lines.append(f"- **[{severity}]** {rule} ({contract}): {message}")

        return BriefingSection(
            title="On-Chain Alerts (Sentinel)",
            content="\n".join(lines),
            priority=Priority.HIGH,
        )
    except Exception:
        return None


def gather_digest_summary(project: str) -> BriefingSection | None:
    """Summarize recent digest activity for project-related topics."""
    db_path = Path.home() / ".local" / "share" / "digest" / "feed.db"
    if not db_path.exists():
        return None

    try:
        import sqlite3

        conn = sqlite3.connect(str(db_path))
        rows = conn.execute(
            "SELECT topic, item_count, generated_at FROM digests ORDER BY generated_at DESC LIMIT 5"
        ).fetchall()
        conn.close()

        if not rows:
            return None

        lines: list[str] = []
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


def gather_ci_status(repo: str) -> BriefingSection | None:
    """Last CI run result."""
    if not which("gh"):
        return None

    output = _run(["gh", "run", "list", "--repo", repo, "--limit", "1"])
    if not output:
        return None

    return BriefingSection(
        title="CI Status",
        content=f"```\n{output}\n```",
        priority=Priority.MEDIUM,
    )
