"""Tests for the watch loop and TOML config."""

from __future__ import annotations

from pathlib import Path

import pytest

from digest.watcher import (
    TopicWatch,
    WatchConfig,
)


@pytest.fixture()
def config_path(tmp_path: Path) -> Path:
    toml_content = """\
poll_interval_minutes = 15
synthesize = true

[notifications]
macos = false
log_file = "/tmp/test-alerts.jsonl"

[[topics]]
name = "noir zk proofs"
platforms = "hn,github,ethresearch"
days = 7

[topics.thresholds]
min_engagement = 100
min_new_items = 3

[topics.triggers]
new_governance_proposal = false

[[topics]]
name = "snapshot governance"
platforms = "snapshot"
days = 3

[topics.thresholds]
accelerating_count = 1
credibility_floor = "verified"

[topics.triggers]
new_governance_proposal = true
"""
    path = tmp_path / "watch.toml"
    path.write_text(toml_content)
    return path


class TestWatchConfig:
    def test_loads_from_toml(self, config_path: Path) -> None:
        cfg = WatchConfig.from_toml(config_path)
        assert cfg.poll_interval_minutes == 15
        assert cfg.synthesize is True
        assert len(cfg.topics) == 2

    def test_first_topic(self, config_path: Path) -> None:
        cfg = WatchConfig.from_toml(config_path)
        topic = cfg.topics[0]
        assert topic.name == "noir zk proofs"
        assert topic.platforms == "hn,github,ethresearch"
        assert topic.days == 7
        assert topic.thresholds.min_engagement == 100
        assert topic.thresholds.min_new_items == 3

    def test_second_topic_triggers(self, config_path: Path) -> None:
        cfg = WatchConfig.from_toml(config_path)
        topic = cfg.topics[1]
        assert topic.name == "snapshot governance"
        assert topic.triggers.new_governance_proposal is True
        assert topic.thresholds.credibility_floor == "verified"

    def test_notification_config(self, config_path: Path) -> None:
        cfg = WatchConfig.from_toml(config_path)
        assert cfg.notifications.macos is False
        assert cfg.notifications.log_file == "/tmp/test-alerts.jsonl"

    def test_defaults(self) -> None:
        cfg = WatchConfig()
        assert cfg.poll_interval_minutes == 60
        assert cfg.synthesize is False
        assert cfg.topics == []
        assert cfg.notifications.macos is True

    def test_topic_defaults(self) -> None:
        topic = TopicWatch(name="test")
        assert topic.platforms == "hn,github"
        assert topic.days == 7
        assert topic.thresholds.min_engagement == 0
        assert topic.triggers.new_governance_proposal is False

    def test_minimal_toml(self, tmp_path: Path) -> None:
        path = tmp_path / "minimal.toml"
        path.write_text("""\
[[topics]]
name = "rust"
""")
        cfg = WatchConfig.from_toml(path)
        assert len(cfg.topics) == 1
        assert cfg.topics[0].name == "rust"
        assert cfg.poll_interval_minutes == 60
