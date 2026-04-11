"""Typer CLI entry point for the autoresearch agent."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from autoresearch.models import Direction, ExperimentConfig, Status
from autoresearch.runner import execute_run, git_create_branch
from autoresearch.state import (
    DEFAULT_STATE_FILE,
    format_results_table,
    load_state,
    save_config,
)

app = typer.Typer(help="Domain-agnostic autonomous experiment runner", no_args_is_help=True)
console = Console()
err = Console(stderr=True)


@app.command()
def init(
    name: Annotated[str, typer.Argument(help="Experiment name (used as branch suffix)")],
    objective: Annotated[str, typer.Option("--objective", "-o", help="What to optimize")],
    metric: Annotated[str, typer.Option("--metric", "-m", help="Primary metric name")],
    verify: Annotated[str, typer.Option("--verify", "-v", help="Shell command to run experiment")],
    direction: Annotated[Direction, typer.Option("--direction", "-d")] = Direction.LOWER,
    metric_unit: Annotated[str, typer.Option("--unit")] = "",
    time_budget: Annotated[int, typer.Option("--budget", help="Max seconds per run")] = 300,
    mutable: Annotated[
        list[str], typer.Option("--mutable", help="Files the agent can modify")
    ] = [],
    readonly: Annotated[list[str], typer.Option("--readonly", help="Files for context only")] = [],
    guard: Annotated[
        str | None, typer.Option("--guard", help="Safety command that must pass")
    ] = None,
    pattern: Annotated[
        str, typer.Option("--pattern", help="Regex for metric extraction")
    ] = r"METRIC\s+(\S+)=(\S+)",
    state_file: Annotated[Path, typer.Option("--state", hidden=True)] = Path(DEFAULT_STATE_FILE),
    work_dir: Annotated[Path, typer.Option("--dir", hidden=True)] = Path("."),
) -> None:
    """Initialize a new experiment."""
    config = ExperimentConfig(
        name=name,
        objective=objective,
        metric_name=metric,
        metric_unit=metric_unit,
        direction=direction,
        verify_command=verify,
        metric_pattern=pattern,
        mutable_files=list(mutable),
        readonly_files=list(readonly),
        time_budget_seconds=time_budget,
        guard_command=guard,
    )

    state_path = work_dir / state_file
    save_config(state_path, config)

    try:
        git_create_branch(work_dir, name)
        console.print(f"Created branch autoresearch/{name}")
    except Exception:
        err.print("[yellow]Could not create branch (may already exist)[/yellow]")

    console.print(f"Initialized experiment '{name}'")
    console.print(f"  Metric: {metric} ({direction.value} is better)")
    console.print(f"  Verify: {verify}")
    console.print(f"  Budget: {time_budget}s per run")
    if mutable:
        console.print(f"  Mutable: {', '.join(mutable)}")
    console.print(f"\nState file: {state_path}")
    console.print("Run 'autoresearch run' to execute the next iteration.")


@app.command()
def run(
    description: Annotated[
        str, typer.Argument(help="Description of this run's change")
    ] = "baseline",
    state_file: Annotated[Path, typer.Option("--state", hidden=True)] = Path(DEFAULT_STATE_FILE),
    work_dir: Annotated[Path, typer.Option("--dir", hidden=True)] = Path("."),
) -> None:
    """Execute a single experiment run."""
    state_path = work_dir / state_file
    state = load_state(state_path)
    if state is None:
        err.print("[red]No experiment initialized. Run 'autoresearch init' first.[/red]")
        raise typer.Exit(1)

    result = execute_run(state, description, work_dir, state_path)

    if result.status == Status.CRASH:
        console.print(f"[red]Run #{result.run}: CRASH[/red] -- {result.description}")
    elif result.status == Status.DISCARD:
        console.print(
            f"[yellow]Run #{result.run}: DISCARD[/yellow] ({result.metric}) -- {result.description}"
        )
    elif result.status == Status.BASELINE:
        console.print(
            f"[blue]Run #{result.run}: BASELINE[/blue] ({result.metric}) -- {result.description}"
        )
    else:
        console.print(
            f"[green]Run #{result.run}: KEEP[/green] ({result.metric}) -- {result.description}"
        )

    if state.best_metric is not None:
        console.print(
            f"Best: {state.config.metric_name} = {state.best_metric} (run #{state.best_run})"
        )


@app.command()
def loop(
    iterations: Annotated[
        int, typer.Option("--iterations", "-n", help="Max iterations (0 = infinite)")
    ] = 0,
    model: Annotated[
        str, typer.Option("--model", help="Claude model for hypothesis generation")
    ] = "claude-sonnet-4-6",
    state_file: Annotated[Path, typer.Option("--state", hidden=True)] = Path(DEFAULT_STATE_FILE),
    work_dir: Annotated[Path, typer.Option("--dir", hidden=True)] = Path("."),
) -> None:
    """Run the autonomous agent loop: hypothesis -> experiment -> evaluate -> repeat."""
    from autoresearch.agent import get_next_change

    state_path = work_dir / state_file
    state = load_state(state_path)
    if state is None:
        err.print("[red]No experiment initialized. Run 'autoresearch init' first.[/red]")
        raise typer.Exit(1)

    # Run baseline if no results yet
    if not state.results:
        console.print("[blue]Running baseline...[/blue]")
        result = execute_run(state, "baseline", work_dir, state_path)
        console.print(f"Baseline: {state.config.metric_name} = {result.metric}")
        if result.status == Status.CRASH:
            err.print("[red]Baseline crashed. Fix the verify command first.[/red]")
            raise typer.Exit(1)

    iteration = 0
    while iterations == 0 or iteration < iterations:
        iteration += 1
        console.print(f"\n[bold]--- Iteration {iteration} ---[/bold]")

        # Read mutable files
        mutable_contents: dict[str, str] = {}
        for f in state.config.mutable_files:
            p = work_dir / f
            if p.exists():
                mutable_contents[f] = p.read_text()

        # Ask Claude for next change
        console.print("[dim]Generating hypothesis...[/dim]")
        try:
            description, file_changes = get_next_change(state, mutable_contents, model=model)
        except Exception as e:
            err.print(f"[red]Agent error: {e}[/red]")
            continue

        console.print(f"Hypothesis: {description}")

        # Apply changes
        for filename, content in file_changes.items():
            if filename in state.config.mutable_files:
                (work_dir / filename).write_text(content)
                console.print(f"  Modified: {filename}")
            else:
                err.print(f"  [yellow]Skipped {filename} (not in mutable files)[/yellow]")

        # Execute run
        result = execute_run(state, description, work_dir, state_path)

        if result.status == Status.CRASH:
            console.print("[red]CRASH[/red] -- will try different approach")
        elif result.status == Status.DISCARD:
            console.print(f"[yellow]DISCARD[/yellow] ({result.metric}) -- reverting")
        elif result.status == Status.KEEP:
            console.print(f"[green]KEEP[/green] ({result.metric}) -- improvement!")

        if state.best_metric is not None:
            console.print(f"Best so far: {state.config.metric_name} = {state.best_metric}")

    console.print("\n[bold]Loop complete.[/bold]")
    console.print(format_results_table(state))


@app.command()
def dashboard(
    state_file: Annotated[Path, typer.Option("--state", hidden=True)] = Path(DEFAULT_STATE_FILE),
    work_dir: Annotated[Path, typer.Option("--dir", hidden=True)] = Path("."),
    output: Annotated[
        Path | None, typer.Option("--output", "-o", help="Write dashboard to file")
    ] = None,
) -> None:
    """Show experiment dashboard."""
    state_path = work_dir / state_file
    state = load_state(state_path)
    if state is None:
        err.print("[red]No experiment initialized.[/red]")
        raise typer.Exit(1)

    table = format_results_table(state)
    if output:
        output.write_text(table)
        console.print(f"Dashboard written to {output}")
    else:
        console.print(table)


@app.command()
def status(
    state_file: Annotated[Path, typer.Option("--state", hidden=True)] = Path(DEFAULT_STATE_FILE),
    work_dir: Annotated[Path, typer.Option("--dir", hidden=True)] = Path("."),
) -> None:
    """Show current experiment status."""
    state_path = work_dir / state_file
    state = load_state(state_path)
    if state is None:
        err.print("[dim]No experiment initialized.[/dim]")
        raise typer.Exit(0)

    cfg = state.config
    console.print(f"[bold]{cfg.name}[/bold]")
    console.print(f"  Objective: {cfg.objective}")
    console.print(f"  Metric: {cfg.metric_name} ({cfg.direction.value})")
    console.print(f"  Runs: {len(state.results)}")
    console.print(f"  Keeps: {sum(1 for r in state.results if r.status == Status.KEEP)}")
    console.print(f"  Crashes: {sum(1 for r in state.results if r.status == Status.CRASH)}")
    if state.best_metric is not None:
        console.print(f"  Best: {state.best_metric} (run #{state.best_run})")


if __name__ == "__main__":
    app()
