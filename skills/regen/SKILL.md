---
name: regen
description: >
  Read Fluidify Regen incidents and extract the join keys needed to pivot from an
  incident into its underlying OTel telemetry. Regen is a self-hosted incident /
  on-call tool with a REST API but no MCP server; this agent makes incidents
  first-class and emits a ready-to-run SigNoz filter hint -- the incident side of
  the incident <-> telemetry loop (SigNoz is the telemetry side).
  TRIGGER when: user asks about Regen incidents, on-call/paging state, "what's on
  fire", incident triage, ack/resolve an incident, or invokes "/regen"; or wants
  the service.name + labels + time window to feed into SigNoz.
  DO NOT TRIGGER when: user is working on the regen agent code itself; or wants to
  query the telemetry directly (use the signoz skill -- regen hands off to it).
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: regen, incidents, on-call, observability, correlation, signoz, otel, mcp
---

# Regen

Incident reader + correlation extractor for [Fluidify Regen](https://github.com/FluidifyAI/Regen)
(self-hosted, AGPLv3 on-call tool). Regen ships a REST API but no MCP server, so
this agent reads incidents first-class and extracts the keys to pivot into SigNoz
telemetry. Symmetric with the `signoz` skill: **regen answers "what broke and
when"; signoz answers "why," from the traces/metrics/logs.**

## What You Get

- Read incidents and ingested alerts (with their `labels`) and timelines
- `regen_correlation_keys` -- extracts `service.name`, correlation labels
  (`chain`, `role`, `address`, `intent_id`, ...), a time window, and a
  ready-to-run SigNoz filter hint
- Optional write tools (ack / resolve / update) behind an explicit flag

## The mini-axol deployment

- `REGEN_BASE_URL` = `http://mini-axol.tail9b2ce8.ts.net:3302` -- **Tailscale must
  be up** (a connection failure is almost always a down tailnet).
- Runs in **open mode** behind the Tailscale ACL (Regen OSS falls through to open
  mode when no cookie/SAML is configured), so no secret is needed -- only
  `REGEN_BASE_URL`. Guardrail: do not create a Regen user or enable SAML, or open
  mode closes and the wrapper breaks.
- Alerts originate from SigNoz on the same host and carry `service.name`, `chain`,
  `role`, etc. -- the labels that make the SigNoz pivot exact.

## MCP tools

Read (always available):

| Tool | Description |
| --- | --- |
| `regen_list_incidents` | List incidents; filter by `status`, `severity`, `created_after/before`, `limit` |
| `regen_get_incident` | One incident + linked alerts (with `labels`) + timeline |
| `regen_list_alerts` | Ingested alerts; filter by `status`, `source`, `limit` |
| `regen_correlation_keys` | Extract `service.name` + labels + time window + SigNoz filter hint |

Write (only when `REGEN_ENABLE_WRITE=1` or `regen serve --write`):

| Tool | Description |
| --- | --- |
| `regen_ack_incident` | Acknowledge an incident |
| `regen_resolve_incident` | Resolve an incident (optional `summary`) |
| `regen_update_incident` | Update `status` / `severity` / `summary` |

Write tools mutate live on-call state -- confirm intent before calling them.

## Correlation workflow (incident -> OTel)

1. A SigNoz alert (e.g. `SolverGasCriticalOptimism`) fires on `mini-axol`, POSTs to
   Regen's webhook, and opens an incident whose `labels` carry `service.name`,
   `chain`, `role`, etc.
2. `regen_correlation_keys(<id>)` pulls those labels + the incident's time window
   and emits a SigNoz filter hint, e.g.:

   ```
   service.name IN (riddler-balance-exporter, riddler-production)
     AND chain='optimism' AND role='solver'
     AND time>=<start> AND time<=<end>
   ```

3. Feed that hint into the `signoz` MCP -- use the window as explicit `start`/`end`
   (unix ms) so telemetry lines up with when the alert fired:
   `signoz_search_logs`, `signoz_aggregate_traces`, `signoz_query_metrics`
   (the `riddler_*` metrics). This closes the loop from incident back to OTel.

The `/signoz:incident_triage alertId=<id>` prompt automates the SigNoz side once
you have the alert rule id.

## CLI Usage

```bash
regen incidents --severity critical   # list (status/severity filters)
regen incident 42                     # inspect one: alerts + timeline
regen alerts --source prometheus      # list ingested alerts
regen correlate 42                    # the correlation-keys step
regen serve                           # MCP server (stdio); add --write for mutations
```

## Configure

| Variable | Required | Purpose |
| --- | --- | --- |
| `REGEN_BASE_URL` | yes | Regen instance URL (origin only; client appends `/api/v1`) |
| `REGEN_SESSION_COOKIE` | no | `oi_session` cookie value (local-auth deploys only) |
| `REGEN_API_TOKEN` | no | `Authorization: Bearer` (forward-compatible) |
| `REGEN_ENABLE_WRITE` | no | `1`/`true` to expose the write tools |

Point Claude Code at a wrapper that injects `REGEN_BASE_URL` from 1Password,
mirroring the `signoz` wrapper:

```json
{ "mcpServers": { "regen": { "command": "regen-mcp-wrapper.sh", "args": [] } } }
```

## Install

```bash
cd agents/regen
pip install -e ".[dev]"
```

## See also

- `signoz` -- the telemetry side of the loop; where correlation keys get queried
- `observability-designer` -- design SLOs and alert rules that open these incidents
- `sentinel` -- on-chain contract monitoring (a different alert source)
