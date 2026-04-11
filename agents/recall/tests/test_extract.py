"""Tests for recall.extract module."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from recall.extract import classify_entry_type, extract_from_logs, extract_tags
from recall.models import EntryType


class TestClassifyEntryType:
    def test_decision_lets_go_with(self) -> None:
        assert classify_entry_type("let's go with pydantic") == EntryType.DECISION

    def test_decision_decided_to(self) -> None:
        assert classify_entry_type("I decided to use SQLite") == EntryType.DECISION

    def test_decision_we_should(self) -> None:
        assert classify_entry_type("we should use zod for validation") == EntryType.DECISION

    def test_decision_the_approach_is(self) -> None:
        assert classify_entry_type("the approach is to use FTS5") == EntryType.DECISION

    def test_gotcha_dont_use(self) -> None:
        assert classify_entry_type("don't use mocks in tests") == EntryType.GOTCHA

    def test_gotcha_avoid(self) -> None:
        assert classify_entry_type("avoid using global state") == EntryType.GOTCHA

    def test_gotcha_never(self) -> None:
        assert classify_entry_type("never push to main directly") == EntryType.GOTCHA

    def test_gotcha_always(self) -> None:
        assert classify_entry_type("always quote shell variables") == EntryType.GOTCHA

    def test_gotcha_root_cause(self) -> None:
        assert classify_entry_type("the root cause was a race condition") == EntryType.GOTCHA

    def test_gotcha_turns_out(self) -> None:
        assert classify_entry_type("turns out the timeout was too low") == EntryType.GOTCHA

    def test_gotcha_the_problem_was(self) -> None:
        assert classify_entry_type("the problem was stale cache") == EntryType.GOTCHA

    def test_gotcha_the_fix_is(self) -> None:
        assert classify_entry_type("the fix is to bump the version") == EntryType.GOTCHA

    def test_gotcha_make_sure_to(self) -> None:
        assert classify_entry_type("make sure to run migrations first") == EntryType.GOTCHA

    def test_pattern_remember_to(self) -> None:
        assert classify_entry_type("remember to run lint before commit") == EntryType.PATTERN

    def test_insight_note(self) -> None:
        assert classify_entry_type("note: FTS5 needs porter tokenizer") == EntryType.INSIGHT

    def test_insight_important(self) -> None:
        assert classify_entry_type("important: set WAL mode for SQLite") == EntryType.INSIGHT

    def test_fallback_insight(self) -> None:
        assert classify_entry_type("just a random message with no patterns") == EntryType.INSIGHT

    def test_decision_takes_priority_over_gotcha(self) -> None:
        # "decided to" (decision) + "avoid" (gotcha) -> decision wins
        assert classify_entry_type("decided to avoid using ORMs") == EntryType.DECISION


class TestExtractTags:
    def test_single_tag(self) -> None:
        assert extract_tags("use Python for scripting") == ["python"]

    def test_multiple_tags(self) -> None:
        tags = extract_tags("deploy the Docker container to AWS with Terraform")
        assert tags == ["aws", "deploy", "docker", "terraform"]

    def test_no_tags(self) -> None:
        assert extract_tags("just a plain message") == []

    def test_deduplicated(self) -> None:
        tags = extract_tags("use rust and then more rust code in Rust")
        assert tags == ["rust"]

    def test_case_insensitive(self) -> None:
        tags = extract_tags("PYTHON and Python and python")
        assert tags == ["python"]

    def test_technical_terms(self) -> None:
        tags = extract_tags("set up GraphQL API with JWT auth over HTTP")
        assert "graphql" in tags
        assert "api" in tags
        assert "jwt" in tags
        assert "auth" in tags
        assert "http" in tags


class TestExtractFromLogs:
    def _write_history(self, tmp_path: Path, records: list[dict]) -> Path:
        history = tmp_path / "history.jsonl"
        with history.open("w") as f:
            for record in records:
                f.write(json.dumps(record) + "\n")
        return history

    def _recent_ts(self, days_ago: int = 0) -> int:
        """Return a millisecond timestamp for N days ago."""
        dt = datetime.now(timezone.utc)
        ts = dt.timestamp() - (days_ago * 86400)
        return int(ts * 1000)

    def test_extracts_decision(self, tmp_path: Path) -> None:
        history = self._write_history(
            tmp_path,
            [
                {
                    "display": "let's go with SQLite for storage",
                    "timestamp": self._recent_ts(1),
                    "project": "/Users/me/CODE/recall",
                    "sessionId": "abc-123",
                },
            ],
        )

        entries = extract_from_logs(days=7, history_path=history)
        assert len(entries) == 1
        assert entries[0].entry_type == EntryType.DECISION
        assert entries[0].project == "recall"
        assert entries[0].source == "session:abc-123"
        assert "sqlite" in entries[0].tags

    def test_filters_by_date_range(self, tmp_path: Path) -> None:
        history = self._write_history(
            tmp_path,
            [
                {
                    "display": "decided to use FTS5",
                    "timestamp": self._recent_ts(2),
                    "project": "/Users/me/CODE/proj",
                    "sessionId": "s1",
                },
                {
                    "display": "decided to use Redis",
                    "timestamp": self._recent_ts(60),
                    "project": "/Users/me/CODE/proj",
                    "sessionId": "s2",
                },
            ],
        )

        entries = extract_from_logs(days=30, history_path=history)
        assert len(entries) == 1
        assert "fts5" not in entries[0].content.lower() or "redis" not in entries[0].content.lower()
        # The 60-day-old entry should be excluded
        assert all("redis" not in e.content.lower() for e in entries)

    def test_filters_by_project(self, tmp_path: Path) -> None:
        history = self._write_history(
            tmp_path,
            [
                {
                    "display": "decided to use pydantic",
                    "timestamp": self._recent_ts(1),
                    "project": "/Users/me/CODE/recall",
                    "sessionId": "s1",
                },
                {
                    "display": "decided to use zod",
                    "timestamp": self._recent_ts(1),
                    "project": "/Users/me/CODE/frontend",
                    "sessionId": "s2",
                },
            ],
        )

        entries = extract_from_logs(days=7, project="recall", history_path=history)
        assert len(entries) == 1
        assert "pydantic" in entries[0].content

    def test_skips_non_matching_messages(self, tmp_path: Path) -> None:
        history = self._write_history(
            tmp_path,
            [
                {
                    "display": "hello world, just a normal message",
                    "timestamp": self._recent_ts(1),
                    "project": "/Users/me/CODE/proj",
                    "sessionId": "s1",
                },
            ],
        )

        entries = extract_from_logs(days=7, history_path=history)
        assert len(entries) == 0

    def test_handles_missing_file(self, tmp_path: Path) -> None:
        entries = extract_from_logs(days=7, history_path=tmp_path / "nonexistent.jsonl")
        assert entries == []

    def test_handles_malformed_json(self, tmp_path: Path) -> None:
        history = tmp_path / "history.jsonl"
        with history.open("w") as f:
            f.write("not valid json\n")
            f.write(
                json.dumps(
                    {
                        "display": "decided to use SQLite",
                        "timestamp": self._recent_ts(1),
                        "project": "/Users/me/CODE/proj",
                        "sessionId": "s1",
                    }
                )
                + "\n"
            )

        entries = extract_from_logs(days=7, history_path=history)
        assert len(entries) == 1

    def test_handles_missing_fields(self, tmp_path: Path) -> None:
        history = self._write_history(
            tmp_path,
            [
                {"timestamp": self._recent_ts(1)},  # no display
                {"display": "decided to use X"},  # no timestamp
            ],
        )

        entries = extract_from_logs(days=7, history_path=history)
        assert len(entries) == 0

    def test_extracts_multiple_types(self, tmp_path: Path) -> None:
        history = self._write_history(
            tmp_path,
            [
                {
                    "display": "decided to use FastAPI",
                    "timestamp": self._recent_ts(1),
                    "project": "/Users/me/CODE/api",
                    "sessionId": "s1",
                },
                {
                    "display": "don't use pickle for serialization",
                    "timestamp": self._recent_ts(1),
                    "project": "/Users/me/CODE/api",
                    "sessionId": "s2",
                },
                {
                    "display": "note: pydantic v2 has breaking changes",
                    "timestamp": self._recent_ts(1),
                    "project": "/Users/me/CODE/api",
                    "sessionId": "s3",
                },
            ],
        )

        entries = extract_from_logs(days=7, history_path=history)
        assert len(entries) == 3
        types = {e.entry_type for e in entries}
        assert EntryType.DECISION in types
        assert EntryType.GOTCHA in types
        assert EntryType.INSIGHT in types
