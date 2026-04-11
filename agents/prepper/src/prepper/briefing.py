"""Briefing assembly and formatting."""

from __future__ import annotations

from pathlib import Path

from prepper.gatherers import (
    gather_ci_status,
    gather_dependency_status,
    gather_digest_summary,
    gather_git_activity,
    gather_github_state,
    gather_recall_context,
    gather_sentinel_alerts,
)
from prepper.models import Briefing, Priority

_PRIORITY_ORDER = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}


def generate_briefing(
    repo_path: str,
    repo: str | None = None,
    project: str | None = None,
) -> Briefing:
    """Run all gatherers and assemble into a Briefing."""
    project_name = project or Path(repo_path).name

    sections = []

    # Always gather git activity
    git_section = gather_git_activity(repo_path)
    if git_section:
        sections.append(git_section)

    # GitHub state requires repo identifier
    if repo:
        gh_section = gather_github_state(repo)
        if gh_section:
            sections.append(gh_section)

        ci_section = gather_ci_status(repo)
        if ci_section:
            sections.append(ci_section)

    # Dependency status
    dep_section = gather_dependency_status(repo_path)
    if dep_section:
        sections.append(dep_section)

    # Recall context
    if project:
        recall_section = gather_recall_context(project)
        if recall_section:
            sections.append(recall_section)

    # Cross-agent context
    sentinel_section = gather_sentinel_alerts()
    if sentinel_section:
        sections.append(sentinel_section)

    digest_section = gather_digest_summary(project_name)
    if digest_section:
        sections.append(digest_section)

    return Briefing(project_name=project_name, sections=sections)


def format_briefing(briefing: Briefing) -> str:
    """Render a Briefing as markdown, sections ordered by priority."""
    lines: list[str] = []
    lines.append(f"# Briefing: {briefing.project_name}")
    lines.append("")
    lines.append(f"Generated: {briefing.generated_at.strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("")

    if not briefing.sections:
        lines.append("No context gathered. This may be a new project or tools are unavailable.")
        return "\n".join(lines)

    sorted_sections = sorted(briefing.sections, key=lambda s: _PRIORITY_ORDER.get(s.priority, 1))

    for section in sorted_sections:
        lines.append(f"## {section.title}")
        lines.append("")
        lines.append(section.content)
        lines.append("")

    return "\n".join(lines)
