---
impact: HIGH
impactDescription: "Complete reference for all ~41 SigNoz MCP tools grouped by signal and function"
tags: "signoz,mcp,tools,reference,observability"
---

## Tools by category

Common conventions: most query tools accept `timeRange` (e.g. `1h`, `6h`, `24h`,
`7d`; defaults vary per tool) or an explicit `start`/`end` in unix ms (which
override `timeRange`). `searchContext` is optional on every tool -- pass the
user's raw question there for better backend results. `limit`/`offset` paginate;
limits above the max are clamped, not rejected.

### Discovery

| Tool | Key args | Description |
| --- | --- | --- |
| `signoz_list_services` | `timeRange` (6h), `limit`(50)/`offset` | List services. Paginate via `pagination.nextOffset` until `hasMore=false` before concluding a service is absent |
| `signoz_get_service_top_operations` | `service`* , `timeRange`(6h), `tags` | Top operations for one service |
| `signoz_list_metrics` | `searchText`, `limit`(50), `timeRange`(1h), `source` | Discover metric names (e.g. `searchText="riddler"`) |
| `signoz_get_top_metrics` | `timeRange`(7d) | Highest-volume metrics (cost/cardinality lens); drop to `3d`/`24h` if it times out |
| `signoz_get_field_keys` | `signal`* (`metrics`/`traces`/`logs`), `searchText`, `metricName`, `fieldContext`, `fieldDataType` | Discover filterable field keys. Use `fieldContext="resource"` to find resource attributes |
| `signoz_get_field_values` | `signal`* , `name`* , `searchText`, `metricName`, `fieldContext` | Discover valid values for a key (e.g. `name="service.name"`) |

### Metrics

| Tool | Key args | Description |
| --- | --- | --- |
| `signoz_query_metrics` | `metricName`* , `metricType`, `timeAggregation`, `spaceAggregation`, `groupBy`, `filter`, `timeRange`(1h), `requestType`(time_series), `reduceTo`, `formula` | Query one metric with aggregation/grouping. Type/temporality auto-fetched if omitted |
| `signoz_execute_builder_query` | `query`* (object) | Run a raw SigNoz query-builder payload (multi-query, formulas). Escape hatch for anything the typed tools can't express |
| `signoz_check_metric_cardinality` | `metricName`* , `timeRange`(7d) | Series/label cardinality for one metric |
| `signoz_check_metric_usage` | `metricNames`* (array), | Where metrics are used (dashboards/alerts) before changing them |

### Logs

| Tool | Key args | Description |
| --- | --- | --- |
| `signoz_search_logs` | `filter`, `service`, `severity`, `searchText`, `timeRange`(1h), `limit`(100)/`offset` | Raw log search. `searchText` uses CONTAINS on body |
| `signoz_aggregate_logs` | `aggregation`* (count/avg/sum/min/max/p50-p99/rate/count_distinct), `aggregateOn`, `groupBy`, `filter`/`service`/`severity`, `orderBy`, `requestType`(scalar), `timeRange`(1h) | Compute stats over logs. Use `requestType=time_series` for "when did it spike" questions |

### Traces

| Tool | Key args | Description |
| --- | --- | --- |
| `signoz_search_traces` | `filter`, `service`, `operation`, `error`(bool), `minDuration`/`maxDuration` (ns), `timeRange`(1h), `limit`(100)/`offset` | Raw trace/span search |
| `signoz_aggregate_traces` | `aggregation`* , `aggregateOn` (e.g. `duration_nano`), `groupBy`, `service`/`operation`/`error`/`minDuration`, `requestType`(scalar), `timeRange`(1h) | Stats over spans (counts, p99 duration, error rate) |
| `signoz_get_trace_details` | `traceId`* , `timeRange`(6h) | Full span tree + metadata for one trace |

Durations are **nanoseconds** (`500000000` = 500ms, `2000000000` = 2s).
`error=true` maps to `has_error=true`.

### Alerts

| Tool | Key args | Description |
| --- | --- | --- |
| `signoz_list_alerts` | -- | Currently firing alerts |
| `signoz_list_alert_rules` | -- | Configured alert rules |
| `signoz_get_alert` | rule id | One alert rule's definition |
| `signoz_get_alert_history` | rule id | Firing history for a rule |
| `signoz_create_alert` | `CreateAlertInput` | Create an alert rule (write) |
| `signoz_update_alert` | `UpdateAlertInput` | Update an alert rule (write) |
| `signoz_delete_alert` | rule id | Delete an alert rule (write) |

### Dashboards

| Tool | Description |
| --- | --- |
| `signoz_list_dashboards` | List dashboards |
| `signoz_get_dashboard` | Fetch one dashboard definition |
| `signoz_list_dashboard_templates` | Built-in dashboard templates |
| `signoz_import_dashboard` | Import a dashboard JSON |
| `signoz_create_dashboard` / `signoz_update_dashboard` / `signoz_delete_dashboard` | Write operations |

### Saved views

| Tool | Description |
| --- | --- |
| `signoz_list_views` / `signoz_get_view` | List / fetch saved explorer views |
| `signoz_create_view` / `signoz_update_view` / `signoz_delete_view` | Write operations |

### Notification channels

| Tool | Description |
| --- | --- |
| `signoz_list_notification_channels` / `signoz_get_notification_channel` | List / fetch channels |
| `signoz_create_notification_channel` / `signoz_update_notification_channel` / `signoz_delete_notification_channel` | Write operations |

### Docs

| Tool | Description |
| --- | --- |
| `signoz_search_docs` | Search SigNoz documentation |
| `signoz_fetch_doc` | Fetch a specific doc page |

`*` = required argument. Write tools (create/update/delete/import) mutate the live
SigNoz -- confirm intent before calling them.
