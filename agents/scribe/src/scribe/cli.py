"""Typer CLI for scribe."""

from __future__ import annotations

import json
from pathlib import Path

import typer
from recall.store import Store
from rich.console import Console
from rich.table import Table

from scribe.analyzer import analyze_session
from scribe.extractor import extract_insights
from scribe.session_parser import parse_session
from scribe.watcher import ACTIVITY_LOG, ScribeWatchConfig, watch_loop, watch_once

app = typer.Typer(
    help="Session insight extractor. Watches Claude Code sessions and writes to recall.",
    no_args_is_help=True,
)
console = Console()


def _store(db: Path | None = None) -> Store:
    return Store(db_path=db)


@app.command()
def watch(
    config: Path | None = typer.Option(None, "--config", "-c", help="TOML config file"),
    once: bool = typer.Option(False, "--once", help="Run one poll cycle and exit"),
    idle_minutes: int = typer.Option(10, "--idle-minutes", help="Minutes before a session is idle"),
    interval: int = typer.Option(5, "--interval", "-i", help="Poll interval in minutes"),
    db: Path | None = typer.Option(None, "--db", hidden=True),
) -> None:
    """Watch for idle sessions and extract insights into recall."""
    if config:
        cfg = ScribeWatchConfig.from_toml(config)
    else:
        cfg = ScribeWatchConfig(poll_interval_minutes=interval, idle_minutes=idle_minutes)

    store = _store(db)

    if once:
        activities = watch_once(cfg, store)
        total_added = sum(a.insights_added for a in activities)
        console.print(
            f"Analyzed {len(activities)} session(s), added {total_added} insight(s) to recall"
        )
        store.close()
        return

    try:
        console.print(f"Watching (poll {cfg.poll_interval_minutes}m, idle {cfg.idle_minutes}m)")
        watch_loop(cfg, store, console_print=console.print)
    except KeyboardInterrupt:
        console.print("\nStopped.")
    finally:
        store.close()


@app.command()
def analyze(
    session_id: str = typer.Argument(..., help="Session ID to analyze"),
    project: str | None = typer.Option(None, "--project", "-p", help="Project path"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show insights without writing"),
    db: Path | None = typer.Option(None, "--db", hidden=True),
) -> None:
    """Analyze a specific session and extract insights."""
    if not project:
        console.print("[red]--project is required for analyze[/red]")
        raise typer.Exit(1)

    messages = parse_session(session_id, project)
    if not messages:
        console.print(f"[yellow]No session data found for {session_id}[/yellow]")
        raise typer.Exit(1)

    analysis = analyze_session(messages, session_id, project)
    candidates = extract_insights(analysis)

    table = Table(title=f"Session {session_id}")
    table.add_column("Type", style="cyan")
    table.add_column("Content", max_width=80)
    table.add_column("Tags")

    for entry in candidates:
        table.add_row(
            entry.entry_type.value,
            entry.content[:80] + ("..." if len(entry.content) > 80 else ""),
            ", ".join(entry.tags),
        )

    console.print(table)
    console.print(f"\n{len(candidates)} insight(s) extracted")

    if not dry_run and candidates:
        store = _store(db)
        added = 0
        for entry in candidates:
            try:
                store.add(entry)
                added += 1
            except ValueError:
                pass
        store.close()
        console.print(f"{added} insight(s) written to recall")


@app.command()
def stats(
    days: int = typer.Option(30, "--days", "-d", help="Look back N days"),
    project: str | None = typer.Option(None, "--project", "-p", help="Filter by project"),
) -> None:
    """Show activity statistics from the scribe activity log."""
    log_path = ACTIVITY_LOG
    if not log_path.exists():
        console.print("[yellow]No activity log found. Run 'scribe watch' first.[/yellow]")
        return

    entries = []
    for line in log_path.read_text().strip().splitlines():
        try:
            entries.append(json.loads(line))
        except (json.JSONDecodeError, ValueError):
            continue

    if project:
        entries = [e for e in entries if e.get("project") == project]

    total_sessions = len(entries)
    total_generated = sum(e.get("insights_generated", 0) for e in entries)
    total_added = sum(e.get("insights_added", 0) for e in entries)
    total_deduped = sum(e.get("insights_deduplicated", 0) for e in entries)

    table = Table(title="Scribe Activity")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")

    table.add_row("Sessions analyzed", str(total_sessions))
    table.add_row("Insights generated", str(total_generated))
    table.add_row("Insights added", str(total_added))
    table.add_row("Insights deduplicated", str(total_deduped))

    console.print(table)


@app.command()
def recent(
    limit: int = typer.Option(10, "--limit", "-n", help="Number of recent entries"),
) -> None:
    """Show recent activity from the scribe log."""
    log_path = ACTIVITY_LOG
    if not log_path.exists():
        console.print("[yellow]No activity log found.[/yellow]")
        return

    lines = log_path.read_text().strip().splitlines()
    recent_entries = []
    for line in reversed(lines):
        try:
            recent_entries.append(json.loads(line))
        except (json.JSONDecodeError, ValueError):
            continue
        if len(recent_entries) >= limit:
            break

    table = Table(title=f"Recent Scribe Activity (last {limit})")
    table.add_column("Time", style="dim")
    table.add_column("Session", style="cyan", max_width=12)
    table.add_column("Project")
    table.add_column("Generated", justify="right")
    table.add_column("Added", justify="right")
    table.add_column("Deduped", justify="right")

    for entry in recent_entries:
        table.add_row(
            entry.get("timestamp", "")[:19],
            entry.get("session_id", "")[:12],
            entry.get("project", "-"),
            str(entry.get("insights_generated", 0)),
            str(entry.get("insights_added", 0)),
            str(entry.get("insights_deduplicated", 0)),
        )

    console.print(table)


@app.command()
def serve(
    db: Path | None = typer.Option(None, "--db", hidden=True),
) -> None:
    """Start the MCP server (stdio transport)."""
    from scribe.mcp_server import create_server

    server = create_server(db_path=db)
    server.run(transport="stdio")


if __name__ == "__main__":
    app()
