"""Prepper CLI -- pre-session context builder."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from prepper.briefing import format_briefing, generate_briefing

app = typer.Typer(help="Pre-session context builder. Generates project briefings.")
console = Console()


@app.command()
def brief(
    path: str = typer.Argument(default=".", help="Path to the repository"),
    repo: str | None = typer.Option(None, "--repo", "-r", help="GitHub owner/repo"),
    project: str | None = typer.Option(None, "--project", "-p", help="Project name for recall"),
    output: str | None = typer.Option(None, "--output", "-o", help="Write briefing to file"),
    raw: bool = typer.Option(False, "--raw", help="Print raw markdown instead of rendered"),
    budget: int | None = typer.Option(
        None, "--budget", "-b", help="Token budget (drops low-priority sections to fit)"
    ),
    task: str | None = typer.Option(
        None, "--task", "-t", help="Task hint (boosts relevant sections)"
    ),
) -> None:
    """Generate and display a project briefing."""
    repo_path = str(Path(path).resolve())
    briefing = generate_briefing(repo_path=repo_path, repo=repo, project=project)
    md = format_briefing(briefing, token_budget=budget, task_hint=task)

    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(md)
        console.print(f"Briefing written to {out_path}")
    elif raw:
        print(md)
    else:
        console.print(Markdown(md))


@app.command()
def inject(
    path: str = typer.Argument(default=".", help="Path to the repository"),
    repo: str | None = typer.Option(None, "--repo", "-r", help="GitHub owner/repo"),
    project: str | None = typer.Option(None, "--project", "-p", help="Project name for recall"),
    budget: int | None = typer.Option(
        None, "--budget", "-b", help="Token budget (drops low-priority sections to fit)"
    ),
    task: str | None = typer.Option(
        None, "--task", "-t", help="Task hint (boosts relevant sections)"
    ),
) -> None:
    """Generate briefing and write to .claude/prepper-briefing.md for session context."""
    repo_path = Path(path).resolve()
    briefing = generate_briefing(repo_path=str(repo_path), repo=repo, project=project)
    md = format_briefing(briefing, token_budget=budget, task_hint=task)

    target = repo_path / ".claude" / "prepper-briefing.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(md)
    console.print(f"Briefing injected to {target}")


@app.command()
def watch(
    config: Path | None = typer.Option(None, "--config", "-c", help="Path to prepper-watch.toml"),
    interval: int = typer.Option(5, "--interval", "-i", help="Poll interval in minutes"),
    once: bool = typer.Option(False, "--once", help="Run one cycle and exit"),
) -> None:
    """Monitor cross-agent alert logs and dispatch notifications."""
    from prepper.watcher import PrepperWatchConfig, watch_loop, watch_once

    if config and config.exists():
        cfg = PrepperWatchConfig.from_toml(config)
    else:
        cfg = PrepperWatchConfig(poll_interval_minutes=interval)

    console.print(
        f"Watching {len(cfg.agent_logs)} agent log(s), "
        f"polling every {cfg.poll_interval_minutes} minutes."
    )

    if once:
        new = watch_once(cfg)
        console.print(f"{len(new)} new alert(s) found.")
    else:
        try:
            watch_loop(cfg, console_print=console.print)
        except KeyboardInterrupt:
            console.print("Stopped.")


@app.command()
def alerts(
    limit: int = typer.Option(20, "--limit", "-n", help="Max alerts to show"),
    agent: str | None = typer.Option(None, "--agent", "-a", help="Filter by agent name"),
) -> None:
    """Show recent unified alerts from all agents."""
    from prepper.watcher import read_unified_log

    entries = read_unified_log(limit=limit, agent_filter=agent)
    if not entries:
        console.print("[dim]No alerts found.[/dim]")
        return

    table = Table(title="Cross-Agent Alerts")
    table.add_column("Agent", style="cyan")
    table.add_column("Severity", style="bold")
    table.add_column("Rule")
    table.add_column("Message")
    table.add_column("Time")

    severity_styles = {"critical": "red bold", "high": "red", "medium": "yellow", "low": "blue"}

    for entry in entries:
        severity = entry.get("severity", "info")
        style = severity_styles.get(severity, "dim")
        rule = entry.get("rule_name") or entry.get("rule") or entry.get("check_name", "")
        ts = entry.get("timestamp", "")[:16].replace("T", " ")
        table.add_row(
            entry.get("_agent", "?"),
            f"[{style}]{severity.upper()}[/{style}]",
            rule,
            entry.get("message", ""),
            ts,
        )

    console.print(table)


@app.command()
def serve() -> None:
    """Start the MCP server (stdio transport)."""
    from prepper.mcp_server import create_server

    server = create_server()
    server.run(transport="stdio")


if __name__ == "__main__":
    app()
