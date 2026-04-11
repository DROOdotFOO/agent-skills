"""Tests for prepper models."""

from datetime import datetime, timezone

from prepper.models import Briefing, BriefingSection, Priority


def test_briefing_section_defaults():
    section = BriefingSection(title="Test", content="Some content")
    assert section.priority == Priority.MEDIUM


def test_briefing_section_with_priority():
    section = BriefingSection(title="Urgent", content="Fix this", priority=Priority.HIGH)
    assert section.priority == Priority.HIGH
    assert section.title == "Urgent"
    assert section.content == "Fix this"


def test_briefing_defaults():
    briefing = Briefing(project_name="myproj")
    assert briefing.project_name == "myproj"
    assert briefing.sections == []
    assert isinstance(briefing.generated_at, datetime)
    assert briefing.generated_at.tzinfo == timezone.utc


def test_briefing_with_sections():
    sections = [
        BriefingSection(title="A", content="aaa", priority=Priority.LOW),
        BriefingSection(title="B", content="bbb", priority=Priority.HIGH),
    ]
    briefing = Briefing(project_name="test", sections=sections)
    assert len(briefing.sections) == 2
    assert briefing.sections[0].title == "A"
    assert briefing.sections[1].title == "B"


def test_priority_enum_values():
    assert Priority.HIGH.value == "high"
    assert Priority.MEDIUM.value == "medium"
    assert Priority.LOW.value == "low"
