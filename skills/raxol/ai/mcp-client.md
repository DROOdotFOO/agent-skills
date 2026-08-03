---
title: MCP Client
impact: MEDIUM
impactDescription: MCP integration is supplementary and only needed when consuming external tool servers.
tags: raxol, agent, mcp, client
---

# MCP Client

`Raxol.Agent.McpClient` -- stdio-based MCP client for consuming external tool
servers. Handles initialization handshake, tool discovery, and execution.

```elixir
{:ok, client} = McpClient.start_link(
  name: :fs, command: "npx",
  args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
)

{:ok, tools} = McpClient.list_tools(client)
{:ok, result} = McpClient.call_tool(client, "read_file", %{"path" => "/tmp/x"})
# result: %{content: [%{"type" => "text", "text" => "..."}], is_error: false}

McpClient.stop(client)
```

Tool namespacing: `McpClient.tool_name(:fs, "read_file")` -> `"mcp__fs__read_file"`.
Parse back: `McpClient.parse_tool_name("mcp__fs__read_file")` -> `{:ok, {"fs", "read_file"}}`.

Protocol version: `2024-11-05` (pinned in `Raxol.MCP.Protocol.mcp_protocol_version/0`).
Call timeout: 30s. `McpClient` now delegates to `Raxol.MCP.Client` (raxol_mcp) --
use `Raxol.MCP.Client` directly for new code. Registers in `Raxol.Agent.Registry`
as `{:mcp_client, name}`.

## McpBundle

`Raxol.Agent.McpBundle` -- start a set of external MCP servers from specs and wrap
their tools as `Raxol.Agent.Action.Dynamic` values for the ReAct loop. Console
runtimes bundle a default catalog at provision so the agent advertises a broad
toolset without hand-written Actions.

```elixir
%{tools: tools, servers: servers, failed: failed} =
  McpBundle.load(McpBundle.default_servers(workspace: "/path"))

# Feed tools into the loop; the CALLER owns servers' lifecycle (supervise/stop).
Raxol.Agent.Stream.react(prompt, actions: tools)
```

Loading is FAIL-OPEN per server: a server that fails to start or list tools is
logged and skipped, so one broken/uninstalled server never denies the rest. The
`:ready_timeout` (default 15s) is a SINGLE shared deadline across the whole bundle
-- clients start concurrently, so N slow servers cost ~timeout total, not N*timeout.

Discovered tools are `sensitive: true` unless the spec overrides, so the default
`ToolPolicy.deny_sensitive` authorizer gates a bundled tool until an operator opts
in. Tools namespace as `mcp__<server>__<tool>` and dispatch through the same
authorizer + hook chain as any Action (`Raxol.Agent.Action.ToolConverter`).

`default_servers/1` catalog (every server version-pinned -- boot never fetches an
unpinned "latest"; `npx`/`uvx` must be on PATH):

| Server | Command | Sensitive | Why |
| --- | --- | --- | --- |
| `filesystem` | `npx` | yes | writes |
| `fetch` | `uvx` | yes | arbitrary network / SSRF |
| `git` | `uvx` | yes | repo mutation |
| `time` | `uvx` | no | pure/read-only |
| `sequential_thinking` | `npx` | no | pure/read-only |

`:workspace` (default `"."`) scopes the filesystem server's allowed root.
