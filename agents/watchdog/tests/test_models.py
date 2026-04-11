"""Tests for watchdog models."""

from __future__ import annotations

import tempfile
from pathlib import Path

from watchdog.models import (
    CheckResult,
    RepoConfig,
    RepoHealth,
    Schedule,
    Status,
    Thresholds,
    WatchConfig,
)


def test_check_result_icon_pass():
    r = CheckResult(check_name="test", status=Status.PASS, message="ok")
    assert r.icon == "[+]"


def test_check_result_icon_warn():
    r = CheckResult(check_name="test", status=Status.WARN, message="meh")
    assert r.icon == "[~]"


def test_check_result_icon_fail():
    r = CheckResult(check_name="test", status=Status.FAIL, message="bad")
    assert r.icon == "[-]"


def test_repo_health_overall_pass():
    h = RepoHealth(
        repo="owner/repo",
        checks=[
            CheckResult(check_name="a", status=Status.PASS, message="ok"),
            CheckResult(check_name="b", status=Status.PASS, message="ok"),
        ],
    )
    assert h.overall_status == Status.PASS


def test_repo_health_overall_warn():
    h = RepoHealth(
        repo="owner/repo",
        checks=[
            CheckResult(check_name="a", status=Status.PASS, message="ok"),
            CheckResult(check_name="b", status=Status.WARN, message="meh"),
        ],
    )
    assert h.overall_status == Status.WARN


def test_repo_health_overall_fail_trumps_warn():
    h = RepoHealth(
        repo="owner/repo",
        checks=[
            CheckResult(check_name="a", status=Status.WARN, message="meh"),
            CheckResult(check_name="b", status=Status.FAIL, message="bad"),
        ],
    )
    assert h.overall_status == Status.FAIL


def test_repo_health_empty_checks_is_pass():
    h = RepoHealth(repo="owner/repo")
    assert h.overall_status == Status.PASS


def test_watch_config_from_repos():
    cfg = WatchConfig.from_repos(["owner/a", "owner/b"])
    assert len(cfg.repos) == 2
    assert cfg.repos[0].name == "owner/a"
    assert cfg.repos[1].name == "owner/b"
    assert cfg.thresholds.stale_pr_days == 14
    assert cfg.schedule.interval_minutes == 60


def test_watch_config_from_toml():
    toml_content = """\
[[repos]]
name = "owner/repo"
path = "/tmp/repo"

[thresholds]
stale_pr_days = 7
stale_issue_days = 14

[schedule]
interval_minutes = 30
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        f.flush()
        cfg = WatchConfig.from_toml(Path(f.name))

    assert len(cfg.repos) == 1
    assert cfg.repos[0].name == "owner/repo"
    assert cfg.repos[0].path == "/tmp/repo"
    assert cfg.thresholds.stale_pr_days == 7
    assert cfg.thresholds.stale_issue_days == 14
    assert cfg.schedule.interval_minutes == 30


def test_thresholds_defaults():
    t = Thresholds()
    assert t.stale_pr_days == 14
    assert t.stale_issue_days == 30


def test_schedule_defaults():
    s = Schedule()
    assert s.interval_minutes == 60


def test_repo_config_optional_path():
    r = RepoConfig(name="owner/repo")
    assert r.path is None

    r2 = RepoConfig(name="owner/repo", path="/tmp/repo")
    assert r2.path == "/tmp/repo"
