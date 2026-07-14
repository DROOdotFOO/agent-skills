---
impact: MEDIUM
impactDescription: "Common SigNoz workflows: service triage, latency, metrics, and the regen incident correlation loop"
tags: "signoz,patterns,workflows,correlation,regen,otel"
---

## Usage patterns

Every investigation starts by confirming reachability and the live service names,
then scoping by `service.name` (see the resource-attribute-first rule in SKILL.md).

### Confirm the deployment is reachable

```
1. signoz_list_services(timeRange="1h")
   -> live services; if this errors, Tailscale is almost certainly down
      (signoz_url is a tailnet host), not SigNoz itself.

2. signoz_get_field_values(signal="logs", name="service.name")
   -> exact service names to filter on (Riddler services)
```

### Debug a service's errors

Prefer the built-in prompt `/signoz:debug_service_errors service=<name>`; the
manual equivalent:

```
1. signoz_search_logs(service="<name>", severity="ERROR", timeRange="1h")
   -> recent error logs

2. signoz_aggregate_traces(service="<name>", error=true,
     aggregation="count", groupBy="name", timeRange="1h")
   -> which operations are failing, ranked

3. signoz_get_service_top_operations(service="<name>")
   -> the operation landscape to interpret step 2
```

For "when did the errors spike?" add `requestType="time_series"` to the aggregate
call -- it answers both the count and the timing in one query. Never call the same
aggregate twice for count-then-timing.

### Analyze p99 latency

Prefer `/signoz:latency_analysis service=<name>`; manually:

```
1. signoz_aggregate_traces(service="<name>", aggregation="p99",
     aggregateOn="duration_nano", groupBy="name", timeRange="6h")
   -> p99 span duration per operation (ns; 1e9 = 1s)

2. signoz_get_trace_details(traceId="<id from a slow span>")
   -> full span tree to find where the time goes
```

### Query a metric

```
1. signoz_list_metrics(searchText="riddler")     # discover riddler_* names
2. signoz_query_metrics(metricName="riddler_...", groupBy="service.name",
     filter="service.name = '<name>'", timeRange="6h")
```

Before renaming/dropping a metric, check blast radius:

```
signoz_check_metric_usage(metricNames=["riddler_..."])   # dashboards/alerts using it
signoz_check_metric_cardinality(metricName="riddler_...") # series/label explosion
```

`signoz_execute_builder_query(query={...})` is the escape hatch for multi-query
payloads, cross-query formulas, or anything the typed metric tool can't express --
build the SigNoz query-builder object and pass it through raw.

### Regen incident -> SigNoz correlation loop

The primary workflow on mini-axol. A SigNoz alert (e.g. `SolverGasLowBase`) fires,
POSTs to Regen's webhook, and opens an incident whose `labels` carry
`service.name`, `chain`, `role`, etc. Pivot from incident back to telemetry:

```
1. regen_list_incidents(severity="critical")        # find the incident
2. regen_correlation_keys(<incident_id>)
   -> service.name + labels (chain, role, address, intent_id, ...),
      a time window, and a ready-to-run SigNoz filter hint

3. Feed the hint into the matching signal:
   signoz_search_logs(service="<svc>", filter="<hint>", start=<ms>, end=<ms>)
   signoz_aggregate_traces(service="<svc>", error=true, start=<ms>, end=<ms>)
   signoz_query_metrics(metricName="riddler_<...>", filter="<hint>",
     start=<ms>, end=<ms>)
```

Use the incident's window as explicit `start`/`end` (unix ms) rather than a
relative `timeRange`, so the telemetry lines up with when the alert fired. The
`/signoz:incident_triage alertId=<id>` prompt automates the SigNoz side of this
once you have the alert rule id from `signoz_list_alert_rules`.

## Time ranges and pagination

- Defaults differ per tool (`1h` for logs/metrics, `6h` for services/traces/details,
  `7d` for cost tools). Pass an explicit `timeRange` or `start`/`end` when it matters.
- Follow `pagination.nextOffset` until `hasMore=false` before concluding something
  is absent -- especially with `signoz_list_services`.

## Error handling

- A connection/timeout error on the first call usually means the tailnet is down,
  not SigNoz. Verify Tailscale before retrying.
- Cost tools (`signoz_get_top_metrics`, cardinality) over a `7d` window can time
  out on a busy backend -- retry with `3d`, then `24h`.

## Opt-out: hiding the prompts

The server registers 4 prompts unconditionally (`pkg/prompts/prompts.go`), and
Claude Code has **no** supported way to hide MCP prompts short of disabling the
whole server (`disabledMcpjsonServers`). Recommendation: **keep them** -- they
encode exactly the triage/latency/error/compare flows above.

If the `/signoz:*` palette entries are truly unwanted, strip prompt registration
at build time rather than disabling the server. In `setup-signoz-mcp.sh`, before
`go build`, comment out the single `prompts.RegisterPrompts(s.AddPrompt)` call in
`internal/mcp-server/server.go` (guard it behind e.g. `SIGNOZ_MCP_NO_PROMPTS=1`).
Trade-off: a local patch re-applied on every rebuild, divergence from upstream,
and the loss of 4 useful workflow shortcuts.
