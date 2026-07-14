---
name: signoz
description: >
  SigNoz MCP tool reference for querying a live observability backend (OTel
  metrics, traces, logs) plus alerts, dashboards, saved views, and notification
  channels. Covers all ~41 signoz_* tools, the 4 built-in MCP prompts, the
  resource-attribute-first filtering rule, and the regen incident -> SigNoz
  correlation loop on the mini-axol/Riddler deployment.
  TRIGGER when: user asks to query SigNoz, inspect a service's errors/latency,
  search OTel logs or traces, read/aggregate metrics, triage an alert, or uses
  signoz_* MCP tools; or pivots from a regen incident into telemetry.
  DO NOT TRIGGER when: user wants to DESIGN SLOs/alerts/dashboards conceptually
  (use observability-designer skill), or READ/ack/resolve incidents in Regen
  itself (use the regen agent/skill -- signoz is the telemetry side of that loop).
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: signoz, observability, opentelemetry, otel, metrics, traces, logs, mcp, riddler
---

# SigNoz MCP

Query a **live** SigNoz instance over MCP (server already configured). ~41
`signoz_*` tools across telemetry (metrics/traces/logs), alerts, dashboards,
saved views, notification channels, and docs -- plus 4 built-in workflow prompts.

This skill is for **reading and operating a running SigNoz**. For designing SLOs,
alert thresholds, or dashboards from first principles use `observability-designer`.
For reading/acking incidents use the `regen` agent -- SigNoz is where you land
*after* extracting an incident's correlation keys.

## Two rules that make queries fast (and correct)

**1. Filter by resource attributes first.** Resource attributes (`service.name`,
`k8s.namespace.name`, `host.name`) are indexed and dramatically speed up backend
queries. If you don't already have one:

```
signoz_get_field_keys(signal="logs", fieldContext="resource")   # discover keys
signoz_get_field_values(signal="logs", name="service.name")     # discover values
```

Then always scope queries with a `service` (or `filter: service.name = '...'`).
Do not run broad, unfiltered log/trace scans.

**2. Pick the operator to match intent AND data type.**

| Intent | Operator | Example |
| --- | --- | --- |
| Field exists | `EXISTS` | `trace_id EXISTS` |
| Field absent | `NOT EXISTS` | `k8s.pod.name NOT EXISTS` |
| Exact match | `=` | `service.name = 'frontend'` |
| Exclude (field must exist) | `EXISTS AND !=` | `service.name EXISTS AND service.name != 'redis'` |
| One of several | `IN` | `severity_text IN ('ERROR','WARN','FATAL')` |
| Substring | `LIKE` / `ILIKE` | `body ILIKE '%timeout%'` |
| Containment | `CONTAINS` | `body CONTAINS 'timeout'` |
| Regex | `REGEXP` | `name REGEXP '^grpc\.'` |

Safe operators by type: **bool** `= != EXISTS`; **int64** `= != > >= < <= IN EXISTS`;
**string** all of the above plus `LIKE ILIKE CONTAINS REGEXP IN NOT IN`.

**Caveat:** negative operators (`!=`, `NOT LIKE`, `NOT IN`) only match rows where
the field is present -- rows missing the field are silently dropped. To include
them, OR in a `NOT EXISTS`, or gate with `EXISTS AND !=` when you mean "present
but not X".

**Signal ambiguity:** if it isn't clear whether the answer lives in metrics,
traces, or logs, ask before querying.

## The mini-axol / Riddler deployment

The configured `signoz` MCP points at a self-hosted SigNoz on the tailnet:

- `signoz_url` = `http://mini-axol.tail9b2ce8.ts.net:3301` -- **Tailscale must be up**
  (a connection failure is almost always a down tailnet, not a SigNoz outage).
- Telemetry source is **Riddler** OTel; custom metrics are named `riddler_*`.
- Primary filter is always `service.name`. Start any investigation with
  `signoz_list_services` to confirm reachability and the live service names.

## Tool map (~41 tools)

Full argument detail in [tools-reference.md](tools-reference.md); workflows in
[usage-patterns.md](usage-patterns.md).

| Group | Tools |
| --- | --- |
| Discovery | `signoz_list_services`, `signoz_get_service_top_operations`, `signoz_list_metrics`, `signoz_get_top_metrics`, `signoz_get_field_keys`, `signoz_get_field_values` |
| Metrics | `signoz_query_metrics`, `signoz_execute_builder_query`, `signoz_check_metric_cardinality`, `signoz_check_metric_usage` |
| Logs | `signoz_search_logs`, `signoz_aggregate_logs` |
| Traces | `signoz_search_traces`, `signoz_aggregate_traces`, `signoz_get_trace_details` |
| Alerts | `signoz_list_alerts`, `signoz_list_alert_rules`, `signoz_get_alert`, `signoz_get_alert_history`, `signoz_create_alert`, `signoz_update_alert`, `signoz_delete_alert` |
| Dashboards | `signoz_list_dashboards`, `signoz_get_dashboard`, `signoz_create_dashboard`, `signoz_update_dashboard`, `signoz_delete_dashboard`, `signoz_import_dashboard`, `signoz_list_dashboard_templates` |
| Saved views | `signoz_list_views`, `signoz_get_view`, `signoz_create_view`, `signoz_update_view`, `signoz_delete_view` |
| Notification channels | `signoz_list_notification_channels`, `signoz_get_notification_channel`, `signoz_create_notification_channel`, `signoz_update_notification_channel`, `signoz_delete_notification_channel` |
| Docs | `signoz_search_docs`, `signoz_fetch_doc` |

## Built-in MCP prompts

The server ships 4 slash-command prompts (they surface as `/signoz:<name>`).
They are ready-made workflows, not clutter -- reach for them first when they fit:

| Prompt | Args | Runs |
| --- | --- | --- |
| `/signoz:debug_service_errors` | `service`, `timeRange` | error logs + error-trace aggregate + top operations |
| `/signoz:latency_analysis` | `service`, `timeRange` | p99 latency metrics + trace-duration aggregate + slow ops |
| `/signoz:compare_metrics` | `metricName`, `period1`, `period2` | one metric across two windows to spot regressions |
| `/signoz:incident_triage` | `alertId` | alert details + history + related logs & traces |

These prompts cannot be individually hidden in Claude Code (no supported toggle);
see [usage-patterns.md](usage-patterns.md#opt-out-hiding-the-prompts) for the
optional build-time opt-out and why keeping them is recommended.

## What You Get

- Reference documentation for all ~41 SigNoz MCP tools grouped by signal and function.
- The resource-attribute-first rule and a filter-operator cheat sheet that prevent
  slow scans and silently-dropped rows.
- Concrete workflows including the regen incident -> OTel correlation loop against
  the mini-axol/Riddler deployment.

## See also

- `regen` -- reads Fluidify Regen incidents and emits the `service.name` + labels +
  time window to feed into these tools (the incident side of the loop; see
  [usage-patterns.md](usage-patterns.md#regen-incident---signoz-correlation-loop))
- `observability-designer` -- design SLOs, alert rules, and dashboards conceptually
- `ethskills` -- Ethereum tooling context for the Riddler stack being observed
