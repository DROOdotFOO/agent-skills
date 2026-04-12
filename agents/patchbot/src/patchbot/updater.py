"""Run dependency updates, tests, and create PRs."""

import subprocess
from datetime import datetime, timezone

from patchbot.detector import get_outdated_command
from patchbot.hooks import Verdict, log_hook_result, pre_tool_use
from patchbot.models import Dependency, Ecosystem, UpdatePlan, UpdateResult


def scan_outdated(repo_path: str, ecosystem: Ecosystem) -> list[Dependency]:
    """Run the outdated command for an ecosystem and return dependencies.

    Parses output best-effort. Returns an empty list if the command
    is unavailable or produces unparseable output.
    """
    cmd = get_outdated_command(ecosystem)
    if cmd is None:
        return []

    hook = pre_tool_use(cmd)
    if hook.verdict == Verdict.DENY:
        return []
    log_hook_result(hook)

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []

    output = result.stdout + result.stderr
    return _parse_outdated(output, ecosystem)


def _parse_outdated(output: str, ecosystem: Ecosystem) -> list[Dependency]:
    """Best-effort parse of outdated command output into Dependency list."""
    deps: list[Dependency] = []
    lines = output.strip().splitlines()

    for line in lines:
        line = line.strip()
        if not line or line.startswith(("=", "-", "Package", "Name")):
            continue

        parts = line.split()
        if len(parts) < 2:
            continue

        name = parts[0]
        current = parts[1]
        latest = parts[2] if len(parts) >= 3 else None

        # Skip lines that are clearly headers or noise
        if not any(c.isdigit() for c in current):
            continue

        deps.append(
            Dependency(
                name=name,
                current_version=current,
                latest_version=latest,
                ecosystem=ecosystem,
            )
        )

    return deps


def run_update(repo_path: str, plan: UpdatePlan, dry_run: bool = False) -> UpdateResult:
    """Execute an update plan: run update command, then test command."""
    if dry_run:
        return UpdateResult(plan=plan, success=True, test_passed=True)

    hook = pre_tool_use(plan.update_command)
    if hook.verdict == Verdict.DENY:
        return UpdateResult(plan=plan, success=False, test_passed=False)
    log_hook_result(hook)

    update_result = subprocess.run(
        plan.update_command,
        shell=True,
        cwd=repo_path,
        capture_output=True,
        text=True,
        timeout=300,
    )
    if update_result.returncode != 0:
        return UpdateResult(plan=plan, success=False, test_passed=False)

    test_hook = pre_tool_use(plan.test_command)
    if test_hook.verdict == Verdict.DENY:
        return UpdateResult(plan=plan, success=True, test_passed=False)
    log_hook_result(test_hook)

    test_result = subprocess.run(
        plan.test_command,
        shell=True,
        cwd=repo_path,
        capture_output=True,
        text=True,
        timeout=600,
    )
    return UpdateResult(
        plan=plan,
        success=True,
        test_passed=test_result.returncode == 0,
    )


def create_pr(
    repo_path: str,
    result: UpdateResult,
    base_branch: str = "main",
    dry_run: bool = False,
) -> str | None:
    """Create a branch, commit changes, push, and open a PR via gh CLI.

    Returns the PR URL on success, None on failure.
    """
    if not result.success:
        return None

    eco = result.plan.ecosystem.value
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d-%H%M%S")
    branch = f"patchbot/{eco}-deps-{timestamp}"
    title = f"chore({eco}): update dependencies"
    body = _build_pr_body(result)

    if dry_run:
        return f"(dry-run) would create PR: {title} on branch {branch}"

    commands = [
        f"git checkout -b {branch}",
        "git add -A",
        f'git commit -m "{title}"',
        f"git push -u origin {branch}",
        f'gh pr create --base {base_branch} --title "{title}" --body "{body}"',
    ]

    for cmd in commands:
        cmd_hook = pre_tool_use(cmd)
        if cmd_hook.verdict == Verdict.DENY:
            return None
        log_hook_result(cmd_hook)

        proc = subprocess.run(
            cmd,
            shell=True,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if proc.returncode != 0:
            return None

        # Last command output contains the PR URL
        if "gh pr create" in cmd:
            return proc.stdout.strip()

    return None


def _build_pr_body(result: UpdateResult) -> str:
    """Build a PR description from an update result."""
    eco = result.plan.ecosystem.value
    dep_count = len(result.plan.dependencies)
    test_status = "passed" if result.test_passed else "FAILED"

    lines = [
        f"Automated dependency update for **{eco}** ecosystem.",
        "",
        f"- Dependencies checked: {dep_count}",
        f"- Update command: `{result.plan.update_command}`",
        f"- Test command: `{result.plan.test_command}`",
        f"- Tests: {test_status}",
        "",
        "Generated by patchbot.",
    ]
    return "\\n".join(lines)
