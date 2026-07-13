---
title: MCP Server (Tool Auto-Derivation)
impact: HIGH
impactDescription: Hand-writing MCP tool specs instead of deriving them from the widget tree drifts out of sync with the UI.
tags: raxol, mcp, server, tools, resources
---

# MCP Server (`Raxol.MCP`)

`raxol_mcp` (v2.6) turns a TEA app into an MCP server: tools are auto-derived from the
widget tree, model state is exposed as resources, and a focus lens filters tools by
attention. JSON-RPC 2.0 over stdio + SSE; ETS-backed registry (no GenServer bottleneck).

For consuming *external* MCP servers, see `ai/mcp-client.md`.

## Expose tools from a widget

Implement `Raxol.MCP.ToolProvider` on the module that owns the widget state.

```elixir
defmodule MyApp.SearchWidget do
  @behaviour Raxol.MCP.ToolProvider

  @impl true
  def mcp_tools(_state) do
    [%{
      name: "search",
      description: "Search the index",
      inputSchema: %{type: "object", required: ["q"],
                     properties: %{q: %{type: "string"}}}
    }]
  end

  @impl true
  def handle_tool_call("search", %{"q" => q}, ctx) do
    # ctx: %{widget_id, widget_state, dispatcher_pid}
    {:ok, do_search(q)}                       # or {:ok, result, messages} | {:error, term}
  end
end
```

`Raxol.MCP.ToolProvider.tool_provider?/1` checks whether a module implements it.

## Focus lens (attention-aware filtering)

```elixir
Raxol.MCP.FocusLens.filter(tool_defs,
  mode: :focused,        # :all | :focused | :hover
  focused_id: "search",
  max_tools: 15,
  registry: Raxol.MCP.Registry)
```

Keeps the exposed tool set small and relevant to what the user is looking at.

## Resources (model state as MCP resources)

```elixir
defmodule MyApp do
  @behaviour Raxol.MCP.ResourceProvider

  @impl true
  def mcp_resources do
    [{"cart", fn model -> model.cart end},
     {"user", fn model -> model.user end}]
  end
end
# browsable at raxol://session/{id}/model/{key}
```

`Raxol.MCP.StructuredScreenshot.from_view_tree/2` + `to_json/1` produce a machine-
readable snapshot of the current widget tree (with focus info) for the LLM.

## Test harness (pipe-friendly)

`Raxol.MCP.Test` drives a session through tool calls with functor-law property
coverage. Interaction helpers return the session so they pipe.

```elixir
import Raxol.MCP.Test

test "user can search" do
  start_session(MyApp)
  |> type_into("search_input", "elixir")
  |> click("search_btn")
  |> assert_component("results_table", fn c -> c[:content] != nil end)
  |> stop_session()
end
```

Other helpers: `clear/2`, `select/3`, `toggle/2`, `call_tool/3`, `send_key/3`.
`start_session/2` opts: `:id`, `:width` (120), `:height` (40), `:settle_ms` (100).

## Pitfalls

1. **Hand-maintained tool specs** -- derive from `mcp_tools/1` so tools track the UI.
2. **Exposing every tool at once** -- use `FocusLens` (`max_tools`, `:focused`) or the
   model context blows past useful limits.
3. **Blocking in `handle_tool_call/3`** -- long work should dispatch via the
   `dispatcher_pid` in `ctx` and return, not block the MCP request.
