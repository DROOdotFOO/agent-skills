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
