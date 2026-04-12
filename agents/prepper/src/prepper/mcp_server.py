"""FastMCP server exposing prepper tools for Claude Code integration."""

from __future__ import annotations

from pathlib import Path

from fastmcp import FastMCP

from prepper.briefing import format_briefing, generate_briefing


def create_server() -> FastMCP:
    """Create a FastMCP server with prepper tools."""
    mcp = FastMCP(
        "prepper",
        instructions=(
            "Pre-session context builder. Use prepper_brief to generate a project briefing "
            "covering git activity, GitHub state, CI status, dependencies, and recall context. "
            "Use prepper_inject to write the briefing to .claude/prepper-briefing.md."
        ),
    )

    @mcp.tool()
    def prepper_brief(
        path: str = ".",
        repo: str | None = None,
        project: str | None = None,
        token_budget: int | None = None,
        task_hint: str | None = None,
    ) -> str:
        """Generate a project briefing with git, GitHub, CI, deps, and recall context.

        Args:
            path: Path to the repository (default: current directory)
            repo: GitHub owner/repo identifier for GitHub API checks (optional)
            project: Project name for recall knowledge base queries (optional)
            token_budget: Approximate token limit. Drops LOW sections first, truncates
                MEDIUM sections. HIGH sections always kept. (optional)
            task_hint: Task description to boost relevant MEDIUM sections. Sections
                matching task terms sort higher. (optional)
        """
        repo_path = str(Path(path).resolve())
        briefing = generate_briefing(repo_path=repo_path, repo=repo, project=project)
        return format_briefing(briefing, token_budget=token_budget, task_hint=task_hint)

    @mcp.tool()
    def prepper_inject(
        path: str = ".",
        repo: str | None = None,
        project: str | None = None,
        token_budget: int | None = None,
        task_hint: str | None = None,
    ) -> str:
        """Generate a briefing and write it to .claude/prepper-briefing.md for session context.

        Args:
            path: Path to the repository (default: current directory)
            repo: GitHub owner/repo identifier for GitHub API checks (optional)
            project: Project name for recall knowledge base queries (optional)
            token_budget: Approximate token limit. Drops LOW sections first, truncates
                MEDIUM sections. HIGH sections always kept. (optional)
            task_hint: Task description to boost relevant MEDIUM sections. Sections
                matching task terms sort higher. (optional)
        """
        repo_path = Path(path).resolve()
        briefing = generate_briefing(repo_path=str(repo_path), repo=repo, project=project)
        md = format_briefing(briefing, token_budget=token_budget, task_hint=task_hint)

        target = repo_path / ".claude" / "prepper-briefing.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(md)

        return f"Briefing written to {target}"

    return mcp
