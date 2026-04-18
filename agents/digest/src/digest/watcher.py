"""Watch loop for digest proactive mode.

Loads a TOML config defining topics of interest with alert thresholds
and trigger rules, then polls on a configurable interval.
"""

from __future__ import annotations

import time
from pathlib import Path

from pydantic import BaseModel, Field

from digest.alerts import (
    AlertThresholds,
    DigestAlert,
    TriggerConfig,
    evaluate_thresholds,
    evaluate_triggers,
)
from digest.memory import FeedMemory
from digest.models import DigestRequest
from digest.notifier import DEFAULT_LOG_PATH, append_to_log, notify_macos
from digest.pipeline import run


class TopicWatch(BaseModel):
    """A single topic to watch with its alert configuration."""

    name: str
    platforms: str = "hn,github"
    days: int = 7
    thresholds: AlertThresholds = Field(default_factory=AlertThresholds)
    triggers: TriggerConfig = Field(default_factory=TriggerConfig)


class NotificationConfig(BaseModel):
    """Notification dispatch settings."""

    macos: bool = True
    osascript: bool = True
    log_file: str = str(DEFAULT_LOG_PATH)


class WatchConfig(BaseModel):
    """Full watch configuration loaded from TOML."""

    poll_interval_minutes: int = 60
    synthesize: bool = False
    topics: list[TopicWatch] = Field(default_factory=list)
    notifications: NotificationConfig = Field(default_factory=NotificationConfig)

    @classmethod
    def from_toml(cls, path: Path) -> WatchConfig:
        """Load watch config from a TOML file."""
        from shared.config import load_toml

        raw = load_toml(path)

        topics = []
        for t in raw.get("topics", []):
            topics.append(
                TopicWatch(
                    name=t["name"],
                    platforms=t.get("platforms", "hn,github"),
                    days=t.get("days", 7),
                    thresholds=AlertThresholds(**t.get("thresholds", {})),
                    triggers=TriggerConfig(**t.get("triggers", {})),
                )
            )

        notif_raw = raw.get("notifications", {})
        notifications = NotificationConfig(**notif_raw)

        return cls(
            poll_interval_minutes=raw.get("poll_interval_minutes", 60),
            synthesize=raw.get("synthesize", False),
            topics=topics,
            notifications=notifications,
        )


def watch_once(
    config: WatchConfig,
    *,
    console_print: object | None = None,
) -> list[DigestAlert]:
    """Run one watch cycle: fetch all topics, evaluate alerts, notify.

    Returns all alerts fired during this cycle.
    """
    all_alerts: list[DigestAlert] = []
    log_path = Path(config.notifications.log_file)

    for topic_cfg in config.topics:
        platform_list = [p.strip() for p in topic_cfg.platforms.split(",") if p.strip()]
        request = DigestRequest(
            topic=topic_cfg.name,
            days=topic_cfg.days,
            platforms=platform_list,
            max_items_per_platform=50,
        )

        try:
            result, _ = run(
                request,
                synthesize_narrative=config.synthesize,
                use_expansion=True,
                store_memory=True,
            )
        except Exception as exc:
            if console_print:
                console_print(f"[red]Error fetching '{topic_cfg.name}':[/red] {exc}")
            continue

        # Evaluate thresholds
        mem = FeedMemory()
        try:
            alerts = evaluate_thresholds(result, topic_cfg.thresholds, memory=mem)
            alerts.extend(evaluate_triggers(result, topic_cfg.triggers, memory=mem))
        finally:
            mem.close()

        if alerts:
            all_alerts.extend(alerts)
            append_to_log(alerts, log_path)

            if config.notifications.macos:
                notify_macos(
                    alerts,
                    use_osascript=config.notifications.osascript,
                )

        if console_print:
            status = f"[green]{len(alerts)} alert(s)[/green]" if alerts else "[dim]no alerts[/dim]"
            console_print(f"  {topic_cfg.name}: {status}")

    return all_alerts


def watch_loop(
    config: WatchConfig,
    *,
    console_print: object | None = None,
) -> None:
    """Run the watch loop continuously until interrupted."""
    interval = config.poll_interval_minutes * 60

    while True:
        if console_print:
            console_print(
                f"\n[bold]Watch cycle[/bold] -- "
                f"{len(config.topics)} topic(s), "
                f"interval {config.poll_interval_minutes}m"
            )

        watch_once(config, console_print=console_print)
        time.sleep(interval)
