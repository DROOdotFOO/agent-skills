"""Prepper CLI -- pre-session context builder."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown

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
def serve() -> None:
    """Start the MCP server (stdio transport)."""
    from prepper.mcp_server import create_server

    server = create_server()
    server.run(transport="stdio")


if __name__ == "__main__":
    app()
