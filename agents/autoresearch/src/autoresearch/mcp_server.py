"""FastMCP server exposing autoresearch tools for Claude Code integration."""

from __future__ import annotations

from pathlib import Path

from fastmcp import FastMCP

from autoresearch.state import DEFAULT_STATE_FILE, format_results_table, load_state


def create_server(work_dir: Path | None = None) -> FastMCP:
    """Create a FastMCP server with autoresearch tools."""
    mcp = FastMCP(
        "autoresearch",
        instructions=(
            "Autonomous experiment runner. Use autoresearch_status to check current "
            "experiment progress. Use autoresearch_dashboard for full results table. "
            "Use autoresearch_run to execute the next iteration."
        ),
    )
    base_dir = work_dir or Path(".")

    @mcp.tool()
    def autoresearch_status(
        state_file: str = DEFAULT_STATE_FILE,
    ) -> str:
        """Show current experiment status (name, objective, metric, run count, best result).

        Args:
            state_file: Path to state JSONL file (default: autoresearch.jsonl)
        """
        state_path = base_dir / state_file
        state = load_state(state_path)
        if state is None:
            return "No experiment initialized. Run 'autoresearch init' first."

        cfg = state.config
        lines = [
            f"Experiment: {cfg.name}",
            f"Objective: {cfg.objective}",
            f"Metric: {cfg.metric_name} ({cfg.direction.value} is better)",
            f"Runs: {len(state.results)}",
        ]

        from autoresearch.models import Status

        keeps = sum(1 for r in state.results if r.status == Status.KEEP)
        crashes = sum(1 for r in state.results if r.status == Status.CRASH)
        lines.append(f"Keeps: {keeps}")
        lines.append(f"Crashes: {crashes}")

        if state.best_metric is not None:
            lines.append(f"Best: {cfg.metric_name} = {state.best_metric} (run #{state.best_run})")

        return "\n".join(lines)

    @mcp.tool()
    def autoresearch_dashboard(
        state_file: str = DEFAULT_STATE_FILE,
    ) -> str:
        """Show the full experiment results dashboard as a markdown table.

        Args:
            state_file: Path to state JSONL file (default: autoresearch.jsonl)
        """
        state_path = base_dir / state_file
        state = load_state(state_path)
        if state is None:
            return "No experiment initialized."

        return format_results_table(state)

    @mcp.tool()
    def autoresearch_run(
        description: str = "baseline",
        state_file: str = DEFAULT_STATE_FILE,
    ) -> str:
        """Execute a single experiment run.

        Args:
            description: Description of this run's change (default: "baseline")
            state_file: Path to state JSONL file (default: autoresearch.jsonl)
        """
        from autoresearch.runner import execute_run

        state_path = base_dir / state_file
        state = load_state(state_path)
        if state is None:
            return "No experiment initialized. Run 'autoresearch init' first."

        result = execute_run(state, description, base_dir, state_path)

        lines = [f"Run #{result.run}: {result.status.value}"]
        if result.metric is not None:
            lines.append(f"Metric: {result.metric}")
        lines.append(f"Description: {result.description}")
        if state.best_metric is not None:
            lines.append(
                f"Best so far: {state.config.metric_name} = {state.best_metric} "
                f"(run #{state.best_run})"
            )

        return "\n".join(lines)

    return mcp
