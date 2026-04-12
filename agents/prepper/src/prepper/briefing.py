"""Briefing assembly and formatting."""

from __future__ import annotations

from pathlib import Path

from prepper.gatherers import (
    gather_ci_status,
    gather_dependency_status,
    gather_digest_alerts,
    gather_digest_summary,
    gather_git_activity,
    gather_github_state,
    gather_recall_context,
    gather_sentinel_alerts,
)
from prepper.models import Briefing, BriefingSection, Priority

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

    digest_alerts_section = gather_digest_alerts()
    if digest_alerts_section:
        sections.append(digest_alerts_section)

    return Briefing(project_name=project_name, sections=sections)


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token."""
    return len(text) // 4


def _task_relevance(content: str, task_hint: str) -> int:
    """Count how many task-hint terms appear in content (case-insensitive)."""
    terms = task_hint.lower().split()
    content_lower = content.lower()
    return sum(1 for t in terms if t in content_lower)


def format_briefing(
    briefing: Briefing,
    *,
    token_budget: int | None = None,
    task_hint: str | None = None,
) -> str:
    """Render a Briefing as markdown, sections ordered by priority.

    When token_budget is set, drops LOW sections first, then truncates MEDIUM
    sections to fit. HIGH sections are never dropped. Inspired by Latent Briefing
    adaptive compaction: focused tasks need less context.

    When task_hint is set, MEDIUM sections containing task-hint terms are boosted
    to sort before other MEDIUM sections (task-guided context selection).
    """
    lines: list[str] = []
    lines.append(f"# Briefing: {briefing.project_name}")
    lines.append("")
    lines.append(f"Generated: {briefing.generated_at.strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("")

    if not briefing.sections:
        lines.append("No context gathered. This may be a new project or tools are unavailable.")
        return "\n".join(lines)

    def sort_key(s: BriefingSection) -> tuple[int, int]:
        priority = _PRIORITY_ORDER.get(s.priority, 1)
        relevance = 0
        if task_hint and s.priority == Priority.MEDIUM:
            relevance = -_task_relevance(s.content, task_hint)
        return (priority, relevance)

    sorted_sections = sorted(briefing.sections, key=sort_key)

    if token_budget is not None:
        # Header takes some budget
        header_tokens = _estimate_tokens("\n".join(lines))
        remaining = token_budget - header_tokens

        kept: list[BriefingSection] = []
        for section in sorted_sections:
            section_tokens = (
                _estimate_tokens(section.content) + _estimate_tokens(section.title) + 10
            )
            if section_tokens <= remaining:
                kept.append(section)
                remaining -= section_tokens
            elif section.priority == Priority.HIGH:
                # HIGH sections always kept, even if over budget
                kept.append(section)
                remaining -= section_tokens
            elif section.priority == Priority.MEDIUM and remaining > 50:
                # Truncate MEDIUM sections to fit remaining budget
                char_limit = remaining * 4
                truncated = BriefingSection(
                    title=section.title,
                    content=section.content[:char_limit] + "\n\n[truncated]",
                    priority=section.priority,
                )
                kept.append(truncated)
                remaining = 0
            # LOW sections dropped when over budget
        sorted_sections = kept

    for section in sorted_sections:
        lines.append(f"## {section.title}")
        lines.append("")
        lines.append(section.content)
        lines.append("")

    return "\n".join(lines)
