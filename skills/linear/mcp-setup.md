---
impact: MEDIUM
impactDescription: "Host-specific connection and OAuth recovery for the hosted Linear MCP server"
tags: "linear,mcp,setup,oauth"
---

## Endpoints

| Endpoint                                | Access     |
| --------------------------------------- | ---------- |
| `https://mcp.linear.app/mcp`            | read-write |
| `https://mcp.linear.app/mcp/readonly`   | read-only  |

Auth is OAuth 2.1 with dynamic client registration; the host opens a browser.
No API key is stored in any config file. The read-write resource advertises
`read write`; `/mcp/readonly` advertises only `read` in its protected-resource
metadata, and write tools are rejected there server-side regardless of token
scope. Tokens are cached per host (Claude Code credentials store, Codex
keychain entry `Codex MCP Credentials` keyed by server name + URL, mcp-remote
under `~/.mcp-auth`), so switching endpoints means a fresh login.

For headless clients send `Authorization: Bearer <LINEAR_API_KEY>` instead; a
personal API key carries the permissions it was created with, so create a
`Read`-only key for reporting jobs.

## Managed setup (dotfiles)

`linear = true` and `linear_readonly = false` in `chezmoi.toml` render both the
Claude Code `~/.mcp.json` entry and the Codex `codex mcp add` call. Flip
`linear_readonly` to pin both hosts to `/mcp/readonly`, `chezmoi apply`, then
log in again on each host (the URL is part of the cached credential key).

## Claude Code

```bash
claude mcp add --transport http linear https://mcp.linear.app/mcp
```

or in `~/.mcp.json`:

```json
{
  "mcpServers": {
    "linear": { "type": "http", "url": "https://mcp.linear.app/mcp" }
  }
}
```

Open a session, run `/mcp`, select `linear`, complete the browser login.

## Codex

```bash
codex mcp add linear --url https://mcp.linear.app/mcp
codex mcp login linear
```

Equivalent `~/.codex/config.toml`:

```toml
[mcp_servers.linear]
url = "https://mcp.linear.app/mcp"
```

Linear's docs state older Codex builds need `[features]
experimental_use_rmcp_client = true` for OAuth HTTP servers. Check
`codex mcp list` first; add the flag only if login fails.

## Raxol

`Raxol.MCP.Client` speaks Streamable HTTP directly (needs `mint`), but only
with a static header; it has no OAuth flow. Two options:

Unattended, with the symphony `LINEAR_API_KEY`:

```elixir
{:ok, client} = Raxol.MCP.Client.start_link(
  name: :linear,
  url: "https://mcp.linear.app/mcp/readonly",
  headers: [{"authorization", "Bearer " <> System.fetch_env!("LINEAR_API_KEY")}]
)
```

Interactive OAuth, bridged over stdio with a pinned `mcp-remote` (Raxol's own
bundle pins every npm server; follow that convention):

```elixir
{:ok, client} = Raxol.MCP.Client.start_link(
  name: :linear, command: "npx",
  args: ["-y", "mcp-remote@0.14.3", "https://mcp.linear.app/mcp"]
)
```

mcp-remote caches tokens under `~/.mcp-auth/mcp-remote-<version>/`. If you
hand it a bearer header instead, mcp-remote expands `${LINEAR_API_KEY}` from
its own environment (no shell involved), but the literal still shows in the
process list; prefer `--header-file /path/to/headers.txt` containing
`Authorization: Bearer ...` (mode 0600).

Tools surface as `mcp__linear__<tool>`. `raxol_agent` marks MCP tools
`sensitive: true` by default, and `Raxol.Agent.ToolPolicy.deny_sensitive/0`
(the default authorizer) blocks them until a policy opts them in.

## Recovery

- Stale or rejected token: Claude Code `/mcp` -> `linear` -> clear auth and
  log in again; Codex `codex mcp logout linear && codex mcp login linear`;
  mcp-remote: delete only that server's `~/.mcp-auth/mcp-remote-*/<hash>_*`
  files (wiping the whole directory logs out every mcp-remote server).
- Second workspace with mcp-remote: separate auth context, e.g.
  `MCP_REMOTE_CONFIG_DIR=~/.mcp-auth/work npx -y mcp-remote@0.14.3 https://mcp.linear.app/mcp`.
- Dropped remote connection: disconnect and reconnect from the host; no data impact.
