---
title: Alert Design
impact: CRITICAL
impactDescription: Bad alert design causes fatigue (ignored pages) or blind spots (missed incidents)
tags: alerting,on-call,burn-rate,paging,fatigue-prevention
---

# Alert Design

How to build alerts that catch real problems without burning out the on-call team.

## Severity Classification

| Severity | Response time | Notification | Criteria                                |
|----------|---------------|--------------|------------------------------------------|
| P1       | Immediate     | Page         | User-facing outage, data loss risk       |
| P2       | 30 minutes    | Page         | Degraded experience for many users       |
| P3       | 4 hours       | Ticket       | Minor degradation, workaround exists     |
| P4       | Next business day | Ticket   | Cosmetic, no user impact                 |

Only P1 and P2 should page. Everything else is a ticket.

## Burn Rate Alerting

Instead of alerting on instantaneous error rates (noisy), alert on the rate at which error budget is being consumed.

```
Burn rate = actual error rate / tolerated error rate

Example: SLO = 99.9% (tolerated error rate = 0.1%)
Current error rate = 1% -> burn rate = 10x
At 10x burn rate, the 30-day error budget is exhausted in 3 days.
```

### Multi-window Burn Rate

Use two windows to reduce false positives. Alert only when both conditions are true:

| Alert type | Long window | Short window | Burn rate | Budget consumed |
|------------|-------------|--------------|-----------|-----------------|
| Page       | 1 hour      | 5 minutes    | 14.4x     | 2% in 1h        |
| Page       | 6 hours     | 30 minutes   | 6x        | 5% in 6h        |
| Ticket     | 1 day       | 2 hours      | 3x        | 10% in 1d       |
| Ticket     | 3 days      | 6 hours      | 1x        | 10% in 3d       |

The short window prevents alerting on issues that already recovered. The long window catches sustained problems.

## Fatigue Prevention

### Hysteresis

Add a recovery threshold lower than the trigger threshold. Alert fires at error rate > 1%, resolves at error rate < 0.5%. This prevents flapping when the metric oscillates around the threshold.

### Alert suppression

- **Dependency suppression** -- If database is down, suppress all service alerts that depend on it. Alert only on the root cause.
- **Maintenance suppression** -- Silence alerts during planned maintenance windows.
- **Dedup window** -- Same alert does not re-fire within 15 minutes of the last notification.

### Grouping

Group related alerts into a single notification:
- Same service, multiple instances -> one alert with instance count
- Same root cause, multiple symptoms -> one alert citing the cause
- Cascading failures -> alert on the origin, suppress downstream

### Routing

Route by service ownership and severity:
- P1/P2 -> on-call for the owning team via PagerDuty/Opsgenie
- P3/P4 -> ticket in the owning team's queue
- Cross-service -> route to platform/SRE team

## Alert Rule Testing

Before deploying an alert rule:

1. **Backtest** -- Run the rule against 30 days of historical metrics. Count how many times it would have fired. Verify each firing corresponds to a real incident.
2. **Dry run** -- Deploy in "notify but do not page" mode for 1-2 weeks. Review every firing.
3. **Review quarterly** -- For each alert: how many times did it fire? How many were actionable? Remove or tune alerts with >50% false positive rate.

## Anti-patterns

- **Symptom alerts without cause context** -- "Latency is high" without indicating which dependency is slow. Include diagnostic links in the alert body.
- **Too many alerts** -- If on-call gets >5 pages per shift, alert quality is too low. Consolidate or raise thresholds.
- **No runbook** -- Every paging alert must link to a runbook with: what the alert means, how to diagnose, how to mitigate, who to escalate to.
- **Alerting on metrics you cannot act on** -- If there is no action to take, it is a dashboard panel, not an alert.
- **Static thresholds on seasonal traffic** -- Use anomaly detection or percentage-based thresholds instead of absolute values for metrics that vary by time of day.
