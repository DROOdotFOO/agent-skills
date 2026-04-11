"""Experiment runner: execute verify command, extract metrics, manage git state."""

from __future__ import annotations

import re
import subprocess
import time
from pathlib import Path

from autoresearch.models import (
    Direction,
    ExperimentConfig,
    ExperimentState,
    RunResult,
    Status,
)
from autoresearch.state import save_result


def run_verify(
    config: ExperimentConfig, run_dir: Path
) -> tuple[float | None, dict[str, float], str, float]:
    """Run the verify command and extract metrics.

    Returns (primary_metric, all_metrics, output_tail, duration_seconds).
    """
    log_path = run_dir / "run.log"
    start = time.monotonic()

    try:
        proc = subprocess.run(
            ["bash", "-c", config.verify_command],
            capture_output=True,
            text=True,
            timeout=config.time_budget_seconds + 60,  # Grace period
            cwd=run_dir,
        )
        output = proc.stdout + proc.stderr
    except subprocess.TimeoutExpired:
        duration = time.monotonic() - start
        return None, {}, f"TIMEOUT after {duration:.0f}s", duration

    duration = time.monotonic() - start

    # Write full output to log
    log_path.write_text(output)

    # Extract metrics from output
    metrics = extract_metrics(output, config.metric_pattern)
    primary = metrics.get(config.metric_name)

    # If the command failed and no metric found, it's a crash
    tail = output[-500:] if len(output) > 500 else output

    return primary, metrics, tail, duration


def extract_metrics(output: str, pattern: str) -> dict[str, float]:
    """Extract METRIC name=value pairs from command output."""
    metrics: dict[str, float] = {}
    for match in re.finditer(pattern, output):
        name = match.group(1)
        try:
            value = float(match.group(2))
            metrics[name] = value
        except (ValueError, IndexError):
            continue
    return metrics


def run_guard(config: ExperimentConfig, run_dir: Path) -> bool:
    """Run the guard command if configured. Returns True if it passes."""
    if not config.guard_command:
        return True
    try:
        proc = subprocess.run(
            ["bash", "-c", config.guard_command],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=run_dir,
        )
        return proc.returncode == 0
    except subprocess.TimeoutExpired:
        return False


def git_commit(run_dir: Path, message: str) -> str:
    """Stage all changes and commit. Returns the commit hash."""
    subprocess.run(["git", "add", "-A"], cwd=run_dir, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=run_dir,
        capture_output=True,
        check=True,
    )
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=run_dir,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def git_discard(run_dir: Path) -> None:
    """Discard all uncommitted changes (equivalent to git checkout -- . && git clean -fd)."""
    subprocess.run(["git", "checkout", "--", "."], cwd=run_dir, capture_output=True, check=False)
    subprocess.run(["git", "clean", "-fd"], cwd=run_dir, capture_output=True, check=False)


def git_create_branch(run_dir: Path, name: str) -> None:
    """Create and checkout a new branch."""
    subprocess.run(
        ["git", "checkout", "-b", f"autoresearch/{name}"],
        cwd=run_dir,
        capture_output=True,
        check=True,
    )


def execute_run(
    state: ExperimentState,
    description: str,
    run_dir: Path,
    state_path: Path,
) -> RunResult:
    """Execute a single experiment run.

    1. Commit the current changes
    2. Run the verify command
    3. Extract metrics
    4. Run guard command if configured
    5. Decide keep/discard/crash
    6. Git commit or reset accordingly
    7. Log the result
    """
    run_num = state.current_run
    config = state.config

    # Commit the agent's changes
    try:
        commit_hash = git_commit(run_dir, f"autoresearch run {run_num}: {description}")
    except subprocess.CalledProcessError:
        # Nothing to commit (no changes made)
        commit_hash = ""

    # Run verify command
    primary, metrics, output_tail, duration = run_verify(config, run_dir)

    # Determine status
    if primary is None:
        status = Status.CRASH
    elif not run_guard(config, run_dir):
        status = Status.DISCARD
    elif state.best_metric is None:
        status = Status.BASELINE
    elif (
        config.direction == Direction.LOWER
        and primary < state.best_metric
        or config.direction == Direction.HIGHER
        and primary > state.best_metric
    ):
        status = Status.KEEP
    else:
        status = Status.DISCARD

    result = RunResult(
        run=run_num,
        commit=commit_hash,
        metric=primary,
        metrics=metrics,
        status=status,
        description=description,
        duration_seconds=duration,
    )

    # Git: keep or discard
    if status in (Status.DISCARD, Status.CRASH) and commit_hash:
        # Revert the commit but keep it in history for the log
        subprocess.run(
            ["git", "revert", "--no-edit", "HEAD"],
            cwd=run_dir,
            capture_output=True,
            check=False,
        )

    # Log result
    save_result(state_path, result)

    # Update state
    state.results.append(result)
    state.current_run += 1
    if status in (Status.KEEP, Status.BASELINE):
        state.update_best()

    return result
