---
name: observability-designer
description: |
  SLO/SLI design, alert optimization, and dashboard generation for production services.
  TRIGGER when: user asks to define SLOs, design alerts, create dashboards, reduce alert fatigue, set error budgets, or improve observability; user runs /observability or /slo.
  DO NOT TRIGGER when: debugging a specific incident (use debugging tools), writing application code, configuring CI/CD pipelines.
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: observability,slo,sli,alerting,dashboards,monitoring,sre
---

# Observability Designer Skill

Design production observability from first principles: define what to measure, set targets, build alerts that do not page unnecessarily, and create dashboards that answer questions at a glance.

## Workflow

1. **Define SLIs** -- Identify the indicators that reflect user experience. See [slo-framework.md](slo-framework.md).
2. **Set SLO targets** -- Choose realistic targets based on business requirements and historical data.
3. **Design alerts** -- Build burn-rate alerts that catch real problems without fatigue. See [alert-design.md](alert-design.md).
4. **Create dashboards** -- Organize metrics into role-appropriate views. See [dashboard-design.md](dashboard-design.md).
5. **Iterate** -- Review error budget consumption monthly. Adjust targets and alert thresholds based on operational data.

## Core Principle

Observe from the user's perspective inward:

```
User request -> Load balancer -> API gateway -> Service -> Database
     ^                                                        |
     |_____________ This is what you measure first ___________|
```

Start with the outermost boundary (what the user experiences), then add internal signals only where they help diagnose problems faster.

## Output Format

```
Service: payment-api
SLIs: availability (success rate), latency (P99), throughput
SLO: 99.9% availability over 30-day rolling window
Error budget: 43.2 minutes/month
Alert: burn rate >14.4x over 1h AND >6x over 6h -> page
Dashboard: 4 panels (availability, latency distribution, error rate, saturation)
```

## What You Get

- SLI/SLO definitions with error budgets tailored to business requirements and historical performance data.
- Burn-rate alert configurations designed to minimize false positives and pager fatigue.
- Dashboard layouts organized by role (on-call, product, executive) with actionable panels for availability, latency, and saturation.

## Sub-files

| File                                         | Content                                    |
|----------------------------------------------|--------------------------------------------|
| [slo-framework.md](slo-framework.md)        | SLI definitions, SLO targets, error budgets|
| [alert-design.md](alert-design.md)          | Severity, burn rate, fatigue prevention     |
| [dashboard-design.md](dashboard-design.md)  | Layout, personas, cost optimization        |
