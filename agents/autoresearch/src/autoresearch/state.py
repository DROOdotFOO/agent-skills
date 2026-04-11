"""JSONL state management for experiment tracking."""

from __future__ import annotations

import json
from pathlib import Path

from autoresearch.models import ExperimentConfig, ExperimentState, RunResult

DEFAULT_STATE_FILE = "autoresearch.jsonl"


def save_config(path: Path, config: ExperimentConfig) -> None:
    """Write a config header line to the state file."""
    line = {"type": "config", **config.model_dump(mode="json")}
    with path.open("a") as f:
        f.write(json.dumps(line) + "\n")


def save_result(path: Path, result: RunResult) -> None:
    """Append a result line to the state file."""
    line = {"type": "result", **result.model_dump(mode="json")}
    with path.open("a") as f:
        f.write(json.dumps(line) + "\n")


def load_state(path: Path) -> ExperimentState | None:
    """Load experiment state from a JSONL file.

    Returns None if the file doesn't exist or has no config.
    """
    if not path.exists():
        return None

    config: ExperimentConfig | None = None
    results: list[RunResult] = []

    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            entry_type = data.pop("type", None)
            if entry_type == "config":
                config = ExperimentConfig(**data)
                results = []  # New config resets results (new segment)
            elif entry_type == "result" and config is not None:
                results.append(RunResult(**data))

    if config is None:
        return None

    state = ExperimentState(
        config=config,
        results=results,
        current_run=len(results),
    )
    state.update_best()
    return state


def format_results_table(state: ExperimentState) -> str:
    """Format results as a markdown table for dashboard."""
    cfg = state.config
    lines = [
        f"# {cfg.name} -- Autoresearch Dashboard",
        "",
        f"**Objective:** {cfg.objective}",
        f"**Metric:** {cfg.metric_name} ({cfg.direction.value} is better)",
        f"**Best:** {state.best_metric} (run #{state.best_run})"
        if state.best_metric is not None
        else "**Best:** (no results yet)",
        "",
        "| Run | Metric | Delta | Status | Description |",
        "|-----|--------|-------|--------|-------------|",
    ]

    for r in state.results:
        metric_str = f"{r.metric}" if r.metric is not None else "N/A"
        if r.metric is not None and state.best_metric is not None and r.run > 0:
            baseline = state.results[0].metric
            if baseline is not None and baseline != 0:
                delta = ((r.metric - baseline) / abs(baseline)) * 100
                delta_str = f"{delta:+.1f}%"
            else:
                delta_str = "--"
        else:
            delta_str = "--"
        lines.append(
            f"| {r.run} | {metric_str} | {delta_str} | {r.status.value} | {r.description} |"
        )

    return "\n".join(lines)
