"""Tests for briefing assembly and formatting."""

from prepper.briefing import format_briefing
from prepper.models import Briefing, BriefingSection, Priority


def test_format_empty_briefing():
    briefing = Briefing(project_name="empty")
    md = format_briefing(briefing)
    assert "# Briefing: empty" in md
    assert "No context gathered" in md


def test_format_briefing_with_sections():
    sections = [
        BriefingSection(title="Low", content="low stuff", priority=Priority.LOW),
        BriefingSection(title="High", content="high stuff", priority=Priority.HIGH),
        BriefingSection(title="Med", content="med stuff", priority=Priority.MEDIUM),
    ]
    briefing = Briefing(project_name="test", sections=sections)
    md = format_briefing(briefing)

    assert "# Briefing: test" in md
    assert "## High" in md
    assert "## Med" in md
    assert "## Low" in md

    # High should appear before Low in the output
    high_pos = md.index("## High")
    med_pos = md.index("## Med")
    low_pos = md.index("## Low")
    assert high_pos < med_pos < low_pos


def test_format_briefing_none_sections_filtered():
    """Briefing with only some sections present still formats correctly."""
    sections = [
        BriefingSection(title="Only Section", content="content here", priority=Priority.HIGH),
    ]
    briefing = Briefing(project_name="partial", sections=sections)
    md = format_briefing(briefing)

    assert "# Briefing: partial" in md
    assert "## Only Section" in md
    assert "content here" in md
    assert "No context gathered" not in md


def test_format_briefing_contains_timestamp():
    briefing = Briefing(project_name="ts")
    md = format_briefing(briefing)
    assert "Generated:" in md
    assert "UTC" in md


class TestTokenBudget:
    def test_no_budget_includes_all(self):
        sections = [
            BriefingSection(title="High", content="important" * 100, priority=Priority.HIGH),
            BriefingSection(title="Med", content="medium" * 100, priority=Priority.MEDIUM),
            BriefingSection(title="Low", content="extra" * 100, priority=Priority.LOW),
        ]
        briefing = Briefing(project_name="test", sections=sections)
        md = format_briefing(briefing)
        assert "## High" in md
        assert "## Med" in md
        assert "## Low" in md

    def test_budget_drops_low_first(self):
        sections = [
            BriefingSection(title="High", content="important", priority=Priority.HIGH),
            BriefingSection(title="Med", content="medium info", priority=Priority.MEDIUM),
            BriefingSection(title="Low", content="extra" * 200, priority=Priority.LOW),
        ]
        briefing = Briefing(project_name="test", sections=sections)
        # Small budget should drop the large LOW section
        md = format_briefing(briefing, token_budget=50)
        assert "## High" in md
        assert "## Low" not in md

    def test_budget_never_drops_high(self):
        sections = [
            BriefingSection(title="High", content="critical" * 200, priority=Priority.HIGH),
        ]
        briefing = Briefing(project_name="test", sections=sections)
        # Even with tiny budget, HIGH survives
        md = format_briefing(briefing, token_budget=10)
        assert "## High" in md

    def test_budget_truncates_medium(self):
        sections = [
            BriefingSection(title="High", content="hi", priority=Priority.HIGH),
            BriefingSection(title="Med", content="x" * 2000, priority=Priority.MEDIUM),
        ]
        briefing = Briefing(project_name="test", sections=sections)
        md = format_briefing(briefing, token_budget=100)
        assert "## Med" in md
        assert "[truncated]" in md


class TestTaskHint:
    def test_task_hint_boosts_matching_medium(self):
        sections = [
            BriefingSection(
                title="Dependencies", content="npm audit found 0 issues", priority=Priority.MEDIUM
            ),
            BriefingSection(
                title="Recall", content="auth bug in login flow noted", priority=Priority.MEDIUM
            ),
        ]
        briefing = Briefing(project_name="test", sections=sections)
        md = format_briefing(briefing, task_hint="auth login bug")
        # Recall section should appear before Dependencies because it matches task hint
        recall_pos = md.index("## Recall")
        deps_pos = md.index("## Dependencies")
        assert recall_pos < deps_pos

    def test_task_hint_does_not_affect_priority_order(self):
        sections = [
            BriefingSection(title="Low", content="auth related low", priority=Priority.LOW),
            BriefingSection(title="High", content="git status", priority=Priority.HIGH),
        ]
        briefing = Briefing(project_name="test", sections=sections)
        md = format_briefing(briefing, task_hint="auth")
        # HIGH still before LOW regardless of task match
        high_pos = md.index("## High")
        low_pos = md.index("## Low")
        assert high_pos < low_pos
