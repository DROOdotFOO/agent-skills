"""Tests for prepper.watcher -- cross-agent alert polling."""

from __future__ import annotations

import json
from pathlib import Path

from prepper.watcher import (
    AgentLogConfig,
    NotificationConfig,
    PrepperWatchConfig,
    load_offsets,
    read_unified_log,
    save_offsets,
    watch_once,
)


def _write_alert(path: Path, agent: str, severity: str, message: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(
            json.dumps(
                {
                    "severity": severity,
                    "message": message,
                    "rule_name": f"{agent}_rule",
                    "timestamp": "2026-04-12T12:00:00+00:00",
                }
            )
            + "\n"
        )


def _config(tmp_path: Path, logs: list[AgentLogConfig]) -> PrepperWatchConfig:
    return PrepperWatchConfig(
        poll_interval_minutes=1,
        notifications=NotificationConfig(
            macos=False,
            log_file=tmp_path / "unified.jsonl",
        ),
        agent_logs=logs,
    )


# -- Config tests ------------------------------------------------------------


def test_default_config_has_three_agent_logs():
    cfg = PrepperWatchConfig()
    assert len(cfg.agent_logs) == 3
    names = {log.name for log in cfg.agent_logs}
    assert names == {"digest", "sentinel", "watchdog"}


def test_from_toml(tmp_path):
    toml = tmp_path / "watch.toml"
    toml.write_text(
        "poll_interval_minutes = 10\n"
        "\n"
        "[[agent_logs]]\n"
        'name = "test"\n'
        f'path = "{tmp_path / "test.jsonl"}"\n'
    )
    cfg = PrepperWatchConfig.from_toml(toml)
    assert cfg.poll_interval_minutes == 10
    assert len(cfg.agent_logs) == 1
    assert cfg.agent_logs[0].name == "test"


# -- Offset tests ------------------------------------------------------------


def test_offsets_roundtrip(tmp_path):
    path = tmp_path / "offsets.json"
    offsets = {"/some/file.jsonl": 1024}
    save_offsets(offsets, path)
    loaded = load_offsets(path)
    assert loaded == offsets


def test_load_offsets_missing_file(tmp_path):
    assert load_offsets(tmp_path / "missing.json") == {}


# -- watch_once tests --------------------------------------------------------


def test_watch_once_empty_logs(tmp_path):
    cfg = _config(tmp_path, [])
    result = watch_once(cfg, offsets_path=tmp_path / "offsets.json")
    assert result == []


def test_watch_once_reads_new_lines(tmp_path):
    log = tmp_path / "sentinel.jsonl"
    _write_alert(log, "sentinel", "high", "large transfer")

    cfg = _config(tmp_path, [AgentLogConfig(name="sentinel", path=log)])
    result = watch_once(cfg, offsets_path=tmp_path / "offsets.json")

    assert len(result) == 1
    assert result[0]["_agent"] == "sentinel"
    assert result[0]["message"] == "large transfer"


def test_watch_once_skips_already_read(tmp_path):
    log = tmp_path / "sentinel.jsonl"
    _write_alert(log, "sentinel", "high", "first")

    cfg = _config(tmp_path, [AgentLogConfig(name="sentinel", path=log)])
    offsets_file = tmp_path / "offsets.json"

    # First poll reads the alert
    result1 = watch_once(cfg, offsets_path=offsets_file)
    assert len(result1) == 1

    # Second poll finds nothing new
    result2 = watch_once(cfg, offsets_path=offsets_file)
    assert len(result2) == 0


def test_watch_once_picks_up_appended_lines(tmp_path):
    log = tmp_path / "digest.jsonl"
    _write_alert(log, "digest", "medium", "first")

    cfg = _config(tmp_path, [AgentLogConfig(name="digest", path=log)])
    offsets_file = tmp_path / "offsets.json"

    watch_once(cfg, offsets_path=offsets_file)

    # Append a new alert
    _write_alert(log, "digest", "high", "second")
    result = watch_once(cfg, offsets_path=offsets_file)
    assert len(result) == 1
    assert result[0]["message"] == "second"


def test_watch_once_writes_unified_log(tmp_path):
    log = tmp_path / "watchdog.jsonl"
    _write_alert(log, "watchdog", "high", "CI red")

    unified = tmp_path / "unified.jsonl"
    cfg = _config(tmp_path, [AgentLogConfig(name="watchdog", path=log)])
    cfg.notifications.log_file = unified

    watch_once(cfg, offsets_path=tmp_path / "offsets.json")

    assert unified.exists()
    data = json.loads(unified.read_text().strip())
    assert data["_agent"] == "watchdog"


def test_watch_once_tags_agent_name(tmp_path):
    log = tmp_path / "test.jsonl"
    _write_alert(log, "myagent", "low", "info")

    cfg = _config(tmp_path, [AgentLogConfig(name="myagent", path=log)])
    result = watch_once(cfg, offsets_path=tmp_path / "offsets.json")
    assert result[0]["_agent"] == "myagent"


def test_watch_once_handles_corrupt_lines(tmp_path):
    log = tmp_path / "test.jsonl"
    log.write_text('not-valid-json\n{"severity":"high","message":"ok"}\n')

    cfg = _config(tmp_path, [AgentLogConfig(name="test", path=log)])
    result = watch_once(cfg, offsets_path=tmp_path / "offsets.json")
    assert len(result) == 1
    assert result[0]["message"] == "ok"


def test_watch_once_resets_on_file_shrink(tmp_path):
    log = tmp_path / "test.jsonl"
    _write_alert(log, "test", "high", "first")
    _write_alert(log, "test", "high", "second")

    cfg = _config(tmp_path, [AgentLogConfig(name="test", path=log)])
    offsets_file = tmp_path / "offsets.json"

    # Read both
    watch_once(cfg, offsets_path=offsets_file)

    # Truncate file (simulate rotation)
    log.write_text("")
    _write_alert(log, "test", "high", "after-rotate")

    result = watch_once(cfg, offsets_path=offsets_file)
    assert len(result) == 1
    assert result[0]["message"] == "after-rotate"


def test_watch_once_missing_log_file(tmp_path):
    cfg = _config(tmp_path, [AgentLogConfig(name="ghost", path=tmp_path / "nonexistent.jsonl")])
    result = watch_once(cfg, offsets_path=tmp_path / "offsets.json")
    assert result == []


def test_watch_once_multiple_agents(tmp_path):
    s_log = tmp_path / "sentinel.jsonl"
    w_log = tmp_path / "watchdog.jsonl"
    _write_alert(s_log, "sentinel", "critical", "ownership change")
    _write_alert(w_log, "watchdog", "medium", "stale PRs")

    cfg = _config(
        tmp_path,
        [
            AgentLogConfig(name="sentinel", path=s_log),
            AgentLogConfig(name="watchdog", path=w_log),
        ],
    )
    result = watch_once(cfg, offsets_path=tmp_path / "offsets.json")
    assert len(result) == 2
    agents = {e["_agent"] for e in result}
    assert agents == {"sentinel", "watchdog"}


# -- read_unified_log tests --------------------------------------------------


def test_read_unified_log_empty(tmp_path):
    result = read_unified_log(log_path=tmp_path / "empty.jsonl")
    assert result == []


def test_read_unified_log_newest_first(tmp_path):
    log = tmp_path / "unified.jsonl"
    for i in range(3):
        with log.open("a") as f:
            f.write(
                json.dumps(
                    {
                        "_agent": "test",
                        "severity": "info",
                        "message": f"msg-{i}",
                        "timestamp": f"2026-04-12T1{i}:00:00+00:00",
                    }
                )
                + "\n"
            )

    result = read_unified_log(log_path=log, limit=2)
    assert len(result) == 2
    assert result[0]["message"] == "msg-2"


def test_read_unified_log_agent_filter(tmp_path):
    log = tmp_path / "unified.jsonl"
    for agent in ["sentinel", "watchdog", "sentinel"]:
        with log.open("a") as f:
            f.write(json.dumps({"_agent": agent, "message": agent}) + "\n")

    result = read_unified_log(log_path=log, agent_filter="sentinel")
    assert len(result) == 2
    assert all(e["_agent"] == "sentinel" for e in result)
