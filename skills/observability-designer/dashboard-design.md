---
title: Dashboard Design
impact: HIGH
impactDescription: Poorly designed dashboards waste investigation time and obscure real problems during incidents
tags: dashboards,visualization,metrics,cardinality,cost-optimization
---

# Dashboard Design

Principles for building dashboards that answer questions quickly and scale affordably.

## Information Hierarchy

Structure dashboards top-to-bottom by urgency:

1. **Top row** -- Health at a glance. Red/yellow/green status panels. SLO compliance percentage. Active incidents count.
2. **Middle rows** -- Golden signals: latency, traffic, errors, saturation. Time series with clear baselines.
3. **Bottom rows** -- Deep-dive panels: per-endpoint breakdown, dependency health, resource utilization.

Users scan top-to-bottom. If the top row is green, they stop. If red, they scroll down for diagnosis.

## Cognitive Load

### The 7 +/- 2 Rule

A single dashboard should have 5-9 panels. More than 9 panels means the dashboard is trying to answer too many questions. Split into:

- **Overview dashboard** -- Health summary, golden signals, SLO status (5-7 panels)
- **Deep-dive dashboard** -- Per-service or per-component detail (7-9 panels each)
- **Capacity dashboard** -- Resource utilization, scaling headroom, cost (5-7 panels)

### Panel Design

- One question per panel ("Is latency normal?" not "How is the service doing?")
- Title is the question; visualization is the answer
- Include baseline/threshold lines so deviations are obvious without mental math
- Use consistent time ranges across all panels on a dashboard
- Left Y-axis only (dual Y-axes are almost always misleading)

## Role-based Personas

Different roles need different views:

### SRE / On-call

- Focus: Is anything broken right now?
- Panels: SLO burn rate, active alerts, error rate, saturation
- Refresh: 30 seconds
- Design: High contrast, large numbers, red/green status

### Developer

- Focus: How is my recent deploy performing?
- Panels: Error rate by version, latency by endpoint, log error count, deploy markers
- Refresh: 1 minute
- Design: Time series with deploy annotations, filterable by service/version

### Engineering Manager

- Focus: Are we meeting our reliability targets?
- Panels: SLO compliance trend (weekly/monthly), error budget remaining, DORA metrics, incident count
- Refresh: 5 minutes
- Design: Trend lines, period-over-period comparison, summary statistics

## Visualization Best Practices

| Data type          | Visualization      | Avoid                           |
|--------------------|--------------------|----------------------------------|
| Time series        | Line chart         | Bar chart (too dense at scale)   |
| Current value      | Stat panel / gauge | Time series (hides the answer)   |
| Distribution       | Heatmap / histogram| Averages (hide tail latency)     |
| Proportions        | Stacked area       | Pie chart (hard to compare)      |
| Status             | Status grid        | Time series (binary is not a curve) |
| Top-N              | Bar chart (horizontal) | Table (harder to scan)       |

### Color

- Red = bad, green = good, yellow = warning. Do not invert.
- Use colorblind-safe palettes (avoid red-green only; add shape or pattern cues).
- Gray for baselines and thresholds. Color for current values.

## Cost Optimization

Observability costs grow with three factors: metric cardinality, retention duration, and log volume.

### Metric Retention Tiers

| Tier    | Resolution | Retention | Use case                         |
|---------|------------|-----------|----------------------------------|
| Hot     | 15 seconds | 7 days    | Active dashboards, alert eval    |
| Warm    | 1 minute   | 30 days   | Incident investigation, trends   |
| Cold    | 5 minutes  | 1 year    | Capacity planning, SLO reports   |
| Archive | 1 hour     | 3+ years  | Compliance, auditing             |

Downsample aggressively. P99 latency at 15-second resolution for 1 year costs 10-50x more than tiered retention.

### Cardinality Management

High-cardinality labels (user ID, request ID, trace ID) explode metric storage. Rules:

- Never use unbounded values as metric labels
- Cap label cardinality at ~100 unique values per label
- Use exemplars (link a few sample traces to a metric) instead of high-cardinality labels
- Monitor cardinality growth: `count(count by (__name__)({__name__=~".+"}))`

### Log Sampling

- Sample DEBUG/INFO logs at 1-10% in production
- Keep 100% of WARN/ERROR logs
- Use structured logging (JSON) for machine parsing
- Set per-service log budgets (GB/day) and alert on overruns
