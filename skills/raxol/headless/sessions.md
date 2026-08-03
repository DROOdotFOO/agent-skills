---
title: Headless Sessions
impact: HIGH
impactDescription: Headless mode is the primary interface for AI-driven testing and MCP tool integration.
tags: raxol, headless, testing, mcp
---

# Headless Sessions

`Raxol.Headless` runs TEA apps in `:agent` environment -- no terminal, no IO.
Text screenshots, keystroke injection, and model inspection.

## API

```elixir
# Start from module or file path (compiles, finds first module with view/1)
{:ok, :demo} = Raxol.Headless.start(RaxolDemo, id: :demo)
{:ok, :demo} = Raxol.Headless.start("examples/demo.exs", id: :demo, width: 80, height: 24)
# Default: 120x40

{:ok, text} = Raxol.Headless.screenshot(:demo)           # plain text, no ANSI
:ok = Raxol.Headless.send_key(:demo, :tab)                # special key (atom)
:ok = Raxol.Headless.send_key(:demo, "q")                 # character (string)
:ok = Raxol.Headless.send_key(:demo, "c", ctrl: true)     # with modifier
{:ok, text} = Raxol.Headless.send_key_and_screenshot(:demo, :enter, wait_ms: 100)
{:ok, model} = Raxol.Headless.get_model(:demo)
:ok = Raxol.Headless.stop(:demo)
[:demo] = Raxol.Headless.list()
```

Special keys (atoms): `:tab`, `:enter`, `:escape`, `:backspace`, `:up`, `:down`,
`:left`, `:right`, `:home`, `:end`, `:page_up`, `:page_down`, `:delete`,
`:insert`, `:f1`..`:f12`. Modifiers: `ctrl: true`, `alt: true`, `shift: true`.

INCORRECT:

```elixir
Raxol.Headless.send_key(:demo, "tab")  # wrong: 3-char string, not Tab key
```

CORRECT:

```elixir
Raxol.Headless.send_key(:demo, :tab)   # atom for special keys
```

## MCP Tools (Dev)

When `mix phx.server` is running, six tools are auto-injected into Tidewave
at `localhost:4000/tidewave/mcp`. Server must be running before starting
Claude Code.

| Tool               | Inputs                                 | Returns            |
| ------------------ | -------------------------------------- | ------------------ |
| `raxol_start`      | module OR path, id?, width?, height?   | session id         |
| `raxol_screenshot` | id                                     | plain text screen  |
| `raxol_send_key`   | id, key, ctrl?, alt?, shift?, wait_ms? | updated screen     |
| `raxol_get_model`  | id                                     | inspected model    |
| `raxol_stop`       | id                                     | confirmation       |
| `raxol_list`       | (none)                                 | active session ids |

Typical workflow: start -> screenshot -> send keys -> screenshot -> get model -> stop.

Manual injection: `Raxol.Headless.McpTools.inject_into_tidewave()`.

## MCP Server (Production)

Two paths expose Raxol over MCP; pick by whether a Phoenix app is running:

- **Dev (Tidewave)**: tools ride the running `mix phx.server` HTTP endpoint at
  `localhost:4000/tidewave/mcp` (see above). Requires Phoenix; six headless tools.
- **Standalone stdio**: `mix mcp.server` boots a dedicated JSON-RPC MCP server on
  stdin/stdout -- no Phoenix, no terminal. This is the entry point for Claude
  Code and other MCP clients (`mix.exs` task in the `raxol_mcp` package).

```bash
mix mcp.server   # reads JSON-RPC from stdin, writes responses to stdout
```

Startup is lightweight: it sets `startup_mode: :mcp` and `skip_endpoint: true`,
so the terminal driver, cache, and Phoenix endpoint are skipped. The app still
starts `Raxol.MCP.Supervisor` and `Raxol.Headless`. Logger is redirected to
stderr so it never corrupts the stdout JSON-RPC stream. Transport is
`Raxol.MCP.Transport.Stdio` wrapping `Raxol.MCP.Server`.

Claude Code `.mcp.json`:

```json
{
  "mcpServers": {
    "raxol": {
      "type": "stdio",
      "command": "mix",
      "args": ["mcp.server"],
      "env": { "MIX_ENV": "dev" }
    }
  }
}
```

Unlike Tidewave (six fixed headless tools), the stdio server exposes the full
MCP surface: auto-derived per-Component tools (Button `click`, TextInput
`type_into`) via the focus lens. See [../mcp/server.md](../mcp/server.md).
