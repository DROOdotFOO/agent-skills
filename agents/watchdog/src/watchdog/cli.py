"""Typer CLI entry point for the watchdog agent."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from watchdog.models import RepoConfig, WatchConfig
from watchdog.scanner import format_report, scan_all

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
) -> None:
    """Scan repos and print health report."""
    cfg = _load_config(repos, config, path)
    results = scan_all(cfg)
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
) -> None:
    """Scan repos and write markdown report to file."""
    cfg = _load_config(repos, config, path)
    results = scan_all(cfg)
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
) -> None:
    """Continuous monitoring -- scan on interval."""
    cfg = _load_config(repos, config, path)
    cfg.schedule.interval_minutes = interval

    console.print(f"Watching {len(cfg.repos)} repo(s) every {interval} minutes. Ctrl+C to stop.")

    while True:
        results = scan_all(cfg)
        report_text = format_report(results)
        console.print(report_text)
        console.print(f"[dim]Next scan in {interval} minutes...[/dim]")
        try:
            time.sleep(interval * 60)
        except KeyboardInterrupt:
            console.print("Stopped.")
            raise typer.Exit(0) from None


@app.command()
def serve() -> None:
    """Start the MCP server (stdio transport)."""
    from watchdog.mcp_server import create_server

    server = create_server()
    server.run(transport="stdio")


if __name__ == "__main__":
    app()
