---
title: SLO Framework
impact: CRITICAL
impactDescription: Wrong SLI definitions or unrealistic SLO targets lead to meaningless alerts and wasted engineering time
tags: slo,sli,error-budget,golden-signals,reliability
---

# SLO Framework

How to define Service Level Indicators, set Service Level Objectives, and manage error budgets.

## SLI Definitions by Service Type

### Request-driven services (APIs, web apps)

| SLI          | Definition                                              | Measurement                    |
|--------------|---------------------------------------------------------|--------------------------------|
| Availability | Proportion of successful requests                       | `good_requests / total_requests` |
| Latency      | Proportion of requests faster than threshold            | `requests < Xms / total_requests` |
| Error rate   | Proportion of requests returning errors                 | `error_requests / total_requests` |
| Throughput   | Requests per second within acceptable range             | `current_rps / expected_rps`   |

Latency thresholds should be measured at multiple percentiles:
- **P50** -- Median experience (what most users see)
- **P95** -- Tail experience (1 in 20 users)
- **P99** -- Worst case for non-outliers

### Data pipeline services (ETL, batch, streaming)

| SLI         | Definition                                               |
|-------------|----------------------------------------------------------|
| Freshness   | Time since last successful pipeline completion           |
| Correctness | Proportion of output records that are accurate           |
| Coverage    | Proportion of expected input records processed           |
| Throughput  | Records processed per unit time vs expected              |

### Storage services (databases, caches, object stores)

| SLI          | Definition                                              |
|--------------|---------------------------------------------------------|
| Availability | Proportion of read/write operations that succeed        |
| Latency      | Operation duration at P50/P95/P99                       |
| Durability   | Proportion of stored data retrievable after write ack   |
| Consistency  | Proportion of reads reflecting the most recent write    |

## Setting SLO Targets

### Step 1: Measure current performance

Collect at least 30 days of historical data. Your SLO should be achievable -- slightly below current performance, not aspirational.

### Step 2: Align with business requirements

| Service tier  | Typical availability | Downtime/month |
|---------------|----------------------|----------------|
| Critical      | 99.99%               | 4.3 minutes    |
| Standard      | 99.9%                | 43.2 minutes   |
| Best-effort   | 99.5%                | 3.6 hours      |
| Internal tool | 99.0%                | 7.3 hours      |

Do not set 99.99% unless the business genuinely requires it. Higher targets reduce engineering velocity because every change must be validated against a tighter budget.

### Step 3: Define the window

- **Rolling window** (recommended) -- 30-day rolling. Smooths out spikes, always current.
- **Calendar window** -- Monthly reset. Simpler to explain, but budget resets can create perverse incentives.

## Error Budgets

```
Error budget = 1 - SLO target

Example: SLO = 99.9%
Error budget = 0.1% of requests over 30 days
If 1M requests/day -> 30,000 request failures allowed per month
If measured by time -> 43.2 minutes of downtime allowed per month
```

### Error Budget Policy

Define what happens at each consumption level:

| Budget remaining | Action                                                |
|------------------|-------------------------------------------------------|
| > 50%            | Normal development velocity, ship features            |
| 25-50%           | Increase testing rigor, review recent incidents       |
| 10-25%           | Freeze non-critical changes, focus on reliability     |
| < 10%            | Full reliability focus, only critical fixes ship      |
| Exhausted        | Stop all feature work until budget recovers           |

## Golden Signals

The four golden signals (from Google SRE) provide baseline monitoring for any service:

1. **Latency** -- Duration of requests. Distinguish between successful and failed request latency (failed requests that return fast are misleading).
2. **Traffic** -- Demand on the system. Requests/second for APIs, records/second for pipelines, concurrent sessions for real-time systems.
3. **Errors** -- Rate of failed requests. Include both explicit errors (HTTP 5xx) and implicit errors (HTTP 200 with wrong content, slow responses counted as failures).
4. **Saturation** -- How full the service is. CPU, memory, disk, queue depth, connection pool utilization. Alert before hitting 100%.

Start with golden signals, then add service-specific SLIs as operational maturity increases.
