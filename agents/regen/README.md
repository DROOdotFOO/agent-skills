# Regen

MCP server + CLI for reading [Fluidify Regen](https://github.com/FluidifyAI/Regen)
incidents and correlating them with SigNoz OTel telemetry. Regen is a self-hosted,
AGPLv3 incident-management / on-call tool; it ships a REST API but no MCP server, so this
agent lets Claude read incidents first-class -- symmetric with the `signoz` MCP -- and
extract the join keys needed to pivot from an incident to its underlying traces & metrics.

## Install

```bash
pip install -e ".[dev]"
```

## Configure

The client is pointed at a Regen instance via environment variables:

| Variable | Required | Purpose |
| --- | --- | --- |
| `REGEN_BASE_URL` | yes | Regen instance URL, e.g. `http://mini-axol.tail9b2ce8.ts.net:PORT` |
| `REGEN_SESSION_COOKIE` | no | Value of the `oi_session` cookie (local-auth deploys) |
| `REGEN_API_TOKEN` | no | Sent as `Authorization: Bearer` (forward-compatible; harmless in open mode) |
| `REGEN_ENABLE_WRITE` | no | `1`/`true` to expose the write tools (ack/resolve/update) |

**Auth modes.** Regen OSS v1.0.0 authenticates via a local session cookie (`oi_session`)
or SAML, and falls through to **open mode** when neither is configured. Priority here:
`REGEN_SESSION_COOKIE` (cookie) -> `REGEN_API_TOKEN` (bearer) -> open mode. A
Tailscale-internal instance in open mode needs only `REGEN_BASE_URL`.

## CLI

```bash
# List incidents (filter by status/severity)
REGEN_BASE_URL=http://mini-axol.tail9b2ce8.ts.net:PORT regen incidents --severity critical

# Inspect one incident with its linked alerts + timeline
regen incident 42

# List ingested alerts
regen alerts --source prometheus

# Extract SigNoz-query join keys from an incident (the correlation step)
regen correlate 42

# Run the MCP server (stdio); add --write to enable ack/resolve/update
regen serve
```

## MCP tools

Read (always available):

- `regen_list_incidents(status?, severity?, created_after?, created_before?, limit)`
- `regen_get_incident(incident_id)` -- incident + linked alerts (with `labels`) + timeline
- `regen_list_alerts(status?, source?, limit)`
- `regen_correlation_keys(incident_id)` -- extracts `service.name`, correlation labels
  (`chain`, `role`, `address`, `intent_id`, ...), a time window, and a ready-to-run SigNoz
  filter hint to feed into the `signoz` MCP

Write (only when `REGEN_ENABLE_WRITE=1` or `regen serve --write`):

- `regen_ack_incident(incident_id)`
- `regen_resolve_incident(incident_id, summary?)`
- `regen_update_incident(incident_id, status?, severity?, summary?)`

## Correlation workflow

1. An alert (e.g. `SolverGasLowBase`) fires in SigNoz on `mini-axol` and POSTs to Regen's
   webhook, opening an incident. Its `labels` carry `service.name`, `chain`, `role`, etc.
2. `regen_correlation_keys(<id>)` pulls those labels + the incident's time window and emits
   a SigNoz filter hint.
3. Feed that hint into the `signoz` MCP to pull the matching `riddler_*` metrics / traces,
   closing the loop from incident back to OTel.

## MCP config

Point Claude Code at the server via a wrapper that injects `REGEN_BASE_URL` (and any auth
secret) from 1Password, mirroring the `signoz` wrapper:

```json
{ "mcpServers": { "regen": { "command": "regen-mcp-wrapper.sh", "args": [] } } }
```

## Tests

```bash
pytest
```

No mocks: parsing, correlation extraction, URL/auth builders, config resolution, CLI, and
MCP tool registration are all covered as pure functions against synthetic JSON.
