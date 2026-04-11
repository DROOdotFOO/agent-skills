"""Patchbot CLI -- polyglot dependency updater."""

from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from patchbot.detector import detect_ecosystems, get_test_command, get_update_command
from patchbot.models import Ecosystem, UpdatePlan
from patchbot.updater import create_pr, run_update, scan_outdated

app = typer.Typer(help="Polyglot dependency updater.")
console = Console()


def _resolve_ecosystems(repo_path: str, ecosystem: Ecosystem | None) -> list[Ecosystem]:
    """Detect or filter ecosystems for the given repo."""
    detected = detect_ecosystems(repo_path)
    if not detected:
        console.print("[yellow]No supported ecosystems detected.[/yellow]")
        raise typer.Exit(1)
    if ecosystem is not None:
        if ecosystem not in detected:
            console.print(f"[red]Ecosystem {ecosystem.value} not found in repo.[/red]")
            raise typer.Exit(1)
        return [ecosystem]
    return detected


@app.command()
def scan(
    repo_path: Annotated[str, typer.Option(help="Path to repository")] = ".",
    ecosystem: Annotated[Ecosystem | None, typer.Option(help="Filter to one ecosystem")] = None,
) -> None:
    """Detect ecosystems and list outdated dependencies."""
    ecosystems = _resolve_ecosystems(repo_path, ecosystem)

    console.print(f"Detected ecosystems: {', '.join(e.value for e in ecosystems)}")
    console.print()

    for eco in ecosystems:
        deps = scan_outdated(repo_path, eco)
        if not deps:
            console.print(
                f"[dim]{eco.value}: no outdated dependencies (or command unavailable)[/dim]"
            )
            continue

        table = Table(title=f"{eco.value} -- outdated dependencies")
        table.add_column("Package", style="cyan")
        table.add_column("Current", style="yellow")
        table.add_column("Latest", style="green")
        for dep in deps:
            table.add_row(dep.name, dep.current_version, dep.latest_version or "?")
        console.print(table)
        console.print()


@app.command()
def update(
    repo_path: Annotated[str, typer.Option(help="Path to repository")] = ".",
    ecosystem: Annotated[Ecosystem | None, typer.Option(help="Filter to one ecosystem")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Preview without executing")] = False,
) -> None:
    """Update dependencies and run tests."""
    ecosystems = _resolve_ecosystems(repo_path, ecosystem)

    for eco in ecosystems:
        deps = scan_outdated(repo_path, eco)
        plan = UpdatePlan(
            ecosystem=eco,
            dependencies=deps,
            update_command=get_update_command(eco),
            test_command=get_test_command(eco),
        )
        console.print(f"[bold]{eco.value}[/bold]: updating with `{plan.update_command}`")
        result = run_update(repo_path, plan, dry_run=dry_run)

        if dry_run:
            console.print(f"  [dim](dry run) would update {len(deps)} deps[/dim]")
        elif result.success and result.test_passed:
            console.print("  [green]updated successfully, tests passed[/green]")
        elif result.success:
            console.print("  [yellow]updated but tests failed[/yellow]")
        else:
            console.print("  [red]update failed[/red]")


@app.command()
def pr(
    repo_path: Annotated[str, typer.Option(help="Path to repository")] = ".",
    ecosystem: Annotated[Ecosystem | None, typer.Option(help="Filter to one ecosystem")] = None,
    base_branch: Annotated[str, typer.Option(help="Base branch for PR")] = "main",
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Preview without executing")] = False,
) -> None:
    """Update dependencies, run tests, and create a PR."""
    ecosystems = _resolve_ecosystems(repo_path, ecosystem)

    for eco in ecosystems:
        deps = scan_outdated(repo_path, eco)
        plan = UpdatePlan(
            ecosystem=eco,
            dependencies=deps,
            update_command=get_update_command(eco),
            test_command=get_test_command(eco),
        )
        console.print(f"[bold]{eco.value}[/bold]: updating deps...")
        result = run_update(repo_path, plan, dry_run=dry_run)

        if not result.success:
            console.print("  [red]update failed, skipping PR[/red]")
            continue

        if not result.test_passed:
            console.print("  [yellow]tests failed, skipping PR[/yellow]")
            continue

        pr_url = create_pr(repo_path, result, base_branch=base_branch, dry_run=dry_run)
        if pr_url:
            console.print(f"  [green]PR created: {pr_url}[/green]")
        else:
            console.print("  [red]failed to create PR[/red]")


@app.command()
def serve() -> None:
    """Start the MCP server (stdio transport)."""
    from patchbot.mcp_server import create_server

    server = create_server()
    server.run(transport="stdio")
