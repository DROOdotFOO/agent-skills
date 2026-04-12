"""Typer CLI entry point for the watchdog agent."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table
from shared.notify import append_to_log, notify_macos, read_log_lines
from shared.paths import agent_alert_log

from watchdog.models import RepoConfig, WatchConfig
from watchdog.scanner import alerts_from_health, format_report, scan_all

ALERTS_LOG = agent_alert_log("watchdog")

app = typer.Typer(help="Continuous repo health monitor", no_args_is_help=True)
console = Console()
err = Console(stderr=True)


def _load_config(
    repos: list[str] | None,
    config: Path | None,
    paths: list[str] | None = None,
) -> WatchConfig:
    """Build WatchConfig from CLI args or config file."""
    if config and config.exists():
        cfg = WatchConfig.from_toml(config)
        # CLI repos override config file repos if provided
        if repos:
            cfg.repos = [RepoConfig(name=r) for r in repos]
        return cfg

    if not repos:
        err.print("[red]Provide at least one repo (owner/repo) or --config file.[/red]")
        raise typer.Exit(1)

    repo_configs = []
    path_list = paths or []
    for i, r in enumerate(repos):
        p = path_list[i] if i < len(path_list) else None
        repo_configs.append(RepoConfig(name=r, path=p))

    return WatchConfig(repos=repo_configs)


def _persist_and_notify(results: list, do_notify: bool) -> None:
    """Persist WARN/FAIL results to JSONL and optionally send macOS notifications."""
    for health in results:
        alerts = alerts_from_health(health)
        if alerts:
            append_to_log(alerts, ALERTS_LOG)
            if do_notify:
                for a in alerts:
                    notify_macos(
                        title=f"Watchdog: {a.repo}",
                        body=f"[{a.severity.value.upper()}] {a.check_name}: {a.message}",
                        group=f"watchdog-{a.repo}",
                    )


@app.command()
def scan(
    repos: Annotated[
        list[str] | None,
        typer.Argument(help="Repos to scan (owner/repo)"),
    ] = None,
    config: Annotated[
        Path | None,
        typer.Option("--config", "-c", help="Path to watchdog.toml"),
    ] = None,
    path: Annotated[
        list[str] | None,
        typer.Option("--path", "-p", help="Local path for a repo (same order as repos)"),
    ] = None,
    do_notify: Annotated[
        bool,
        typer.Option("--notify", help="Send macOS notifications for WARN/FAIL"),
    ] = False,
) -> None:
    """Scan repos and print health report."""
    cfg = _load_config(repos, config, path)
    results = scan_all(cfg)
    _persist_and_notify(results, do_notify)
    report = format_report(results)
    console.print(report)


@app.command()
def report(
    repos: Annotated[
        list[str] | None,
        typer.Argument(help="Repos to scan (owner/repo)"),
    ] = None,
    config: Annotated[
        Path | None,
        typer.Option("--config", "-c", help="Path to watchdog.toml"),
    ] = None,
    path: Annotated[
        list[str] | None,
        typer.Option("--path", "-p", help="Local path for a repo"),
    ] = None,
    output: Annotated[
        Path,
        typer.Option("--output", "-o", help="Output file path"),
    ] = Path("watchdog-report.md"),
    do_notify: Annotated[
        bool,
        typer.Option("--notify", help="Send macOS notifications for WARN/FAIL"),
    ] = False,
) -> None:
    """Scan repos and write markdown report to file."""
    cfg = _load_config(repos, config, path)
    results = scan_all(cfg)
    _persist_and_notify(results, do_notify)
    markdown = format_report(results)
    output.write_text(markdown)
    console.print(f"Report written to {output}")


@app.command()
def watch(
    repos: Annotated[
        list[str] | None,
        typer.Argument(help="Repos to scan (owner/repo)"),
    ] = None,
    config: Annotated[
        Path | None,
        typer.Option("--config", "-c", help="Path to watchdog.toml"),
    ] = None,
    path: Annotated[
        list[str] | None,
        typer.Option("--path", "-p", help="Local path for a repo"),
    ] = None,
    interval: Annotated[
        int,
        typer.Option("--interval", "-i", help="Scan interval in minutes"),
    ] = 60,
    do_notify: Annotated[
        bool,
        typer.Option("--notify", help="Send macOS notifications for WARN/FAIL"),
    ] = False,
) -> None:
    """Continuous monitoring -- scan on interval."""
    cfg = _load_config(repos, config, path)
    cfg.schedule.interval_minutes = interval

    console.print(f"Watching {len(cfg.repos)} repo(s) every {interval} minutes. Ctrl+C to stop.")

    while True:
        results = scan_all(cfg)
        _persist_and_notify(results, do_notify)
        report_text = format_report(results)
        console.print(report_text)
        console.print(f"[dim]Next scan in {interval} minutes...[/dim]")
        try:
            time.sleep(interval * 60)
        except KeyboardInterrupt:
            console.print("Stopped.")
            raise typer.Exit(0) from None


@app.command()
def alerts(
    limit: Annotated[
        int,
        typer.Option("--limit", "-n", help="Max alerts to show"),
    ] = 20,
    log_file: Annotated[
        Path | None,
        typer.Option("--file", "-f", help="Alerts log file"),
    ] = None,
) -> None:
    """Show recent watchdog alerts from the JSONL log."""
    path = log_file or ALERTS_LOG
    lines = read_log_lines(path, limit=limit)
    if not lines:
        console.print("[dim]No watchdog alerts found.[/dim]")
        return

    table = Table(title="Recent Watchdog Alerts")
    table.add_column("Severity", style="bold")
    table.add_column("Repo")
    table.add_column("Check")
    table.add_column("Message")
    table.add_column("Time")

    severity_styles = {"critical": "red bold", "high": "red", "medium": "yellow", "low": "blue"}

    for line in lines:
        data = json.loads(line)
        severity = data.get("severity", "info")
        style = severity_styles.get(severity, "dim")
        ts = data.get("timestamp", "")[:16].replace("T", " ")
        table.add_row(
            f"[{style}]{severity.upper()}[/{style}]",
            data.get("repo", ""),
            data.get("check_name", ""),
            data.get("message", ""),
            ts,
        )

    console.print(table)


@app.command()
def serve() -> None:
    """Start the MCP server (stdio transport)."""
    from watchdog.mcp_server import create_server

    server = create_server()
    server.run(transport="stdio")


if __name__ == "__main__":
    app()
