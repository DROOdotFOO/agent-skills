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
No API key is stored in any config file. For headless clients, send
`Authorization: Bearer <LINEAR_API_KEY>` instead (a key created with only the
`Read` permission gives read-only access on either endpoint).

## Managed setup (dotfiles)

`linear = true` and `linear_readonly = false` in `chezmoi.toml` render both the
Claude Code `~/.mcp.json` entry and the Codex `codex mcp add` call. Flip
`linear_readonly` to pin both hosts to `/mcp/readonly`, then `chezmoi apply`.

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

`Raxol.MCP.Client` is stdio-only, so bridge with `mcp-remote` (pin the version;
the Raxol catalog never boots an unpinned package):

```elixir
{:ok, client} = Raxol.MCP.Client.start_link(
  name: :linear, command: "npx",
  args: ["-y", "mcp-remote@0.1.37", "https://mcp.linear.app/mcp"]
)
```

Interactive OAuth caches tokens under `~/.mcp-auth`. For unattended runs reuse
the symphony `LINEAR_API_KEY`:

```elixir
args: ["-y", "mcp-remote@0.1.37", "https://mcp.linear.app/mcp",
       "--header", "Authorization: Bearer ${LINEAR_API_KEY}"]
```

Tools arrive as `mcp__linear__<tool>` and are `sensitive: true` by default, so
the `ToolPolicy.deny_sensitive` authorizer gates them until opted in.

## Recovery

- Internal server error on connect or stale token: `rm -rf ~/.mcp-auth`, reconnect.
- Second workspace: separate auth context, e.g.
  `MCP_REMOTE_CONFIG_DIR=~/.mcp-auth/work npx mcp-remote https://mcp.linear.app/mcp`.
- Dropped remote connection: disconnect and reconnect from the host; no data impact.
