"""Tests for scribe AARTS hooks."""

from scribe.hooks import Verdict, pre_scribe_write


def test_short_content_denied():
    result = pre_scribe_write("too short")
    assert result.verdict == Verdict.DENY
    assert "too short" in result.reason


def test_empty_content_denied():
    result = pre_scribe_write("   ")
    assert result.verdict == Verdict.DENY


def test_tool_output_noise_denied():
    result = pre_scribe_write("File created successfully at: /foo/bar.py")
    assert result.verdict == Verdict.DENY
    assert "noise" in result.reason


def test_install_noise_denied():
    result = pre_scribe_write("Successfully installed package-1.0.0")
    assert result.verdict == Verdict.DENY


def test_requirement_noise_denied():
    result = pre_scribe_write("Requirement already satisfied: pydantic>=2.6.0")
    assert result.verdict == Verdict.DENY


def test_valid_content_allowed():
    result = pre_scribe_write("I prefer pathlib over os.path for all file operations")
    assert result.verdict == Verdict.ALLOW


def test_valid_decision_allowed():
    result = pre_scribe_write("let's go with SQLite for the storage backend")
    assert result.verdict == Verdict.ALLOW
