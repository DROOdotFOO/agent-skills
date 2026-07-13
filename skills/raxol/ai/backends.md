---
title: AI Backends
impact: HIGH
impactDescription: Wrong backend configuration silently produces empty or incorrect LLM responses.
tags: raxol, agent, ai, backend, llm
---

# AI Backends

Pluggable AI model integration via the `Raxol.Agent.AIBackend` behaviour.

## Behaviour

```elixir
@callback complete([%{role: :system | :user | :assistant, content: String.t()}], keyword()) ::
  {:ok, %{content: String.t(), usage: map(), metadata: map()}} | {:error, term()}

@callback stream([message], keyword()) ::
  {:ok, Enumerable.t()} | {:error, term()}  # optional

@callback available?() :: boolean()
@callback name() :: String.t()
@callback capabilities() :: [:completion | :streaming | :tool_use | :vision]
```

Stream events: `{:chunk, text}`, `{:done, response}`, `{:error, reason}`.

Optional callbacks: `handles_tools_internally?/0` (native CLIs that run their own
tool loop) and `max_context_tokens/0`.

## Backend.HTTP

One HTTP client, many providers: `:anthropic`, `:openai`, `:kimi`, `:ollama`, plus
`:openrouter` / `:llm7` via `base_url`. Key opts:
`:provider`, `:auth_token`, `:base_url`, `:model`, `:max_tokens`, `:extra_headers`.

Provider auto-detection from env vars (checked in order):
Lumo -> Anthropic (`ANTHROPIC_API_KEY`) -> Kimi -> OpenAI-compat (`AI_API_KEY`) -> Ollama (`OLLAMA_MODEL`) -> LLM7 (`FREE_AI=true`) -> Mock.

## Harness selection (`Backend.Selector`)

`Raxol.Agent.Backend.Selector.select/1` resolves a named harness to a backend module
+ opts. Harness names -> backend:

| Harness       | Backend                          | Notes                                |
| ------------- | -------------------------------- | ------------------------------------ |
| `anthropic`   | `Backend.HTTP` (`:anthropic`)    |                                      |
| `openai`      | `Backend.HTTP` (`:openai`)       |                                      |
| `kimi`        | `Backend.HTTP` (`:kimi`)         |                                      |
| `ollama`      | `Backend.HTTP` (`:ollama`)       | local                                |
| `openrouter`  | `Backend.HTTP` (openrouter url)  | adds `X-OpenRouter-*` attribution    |
| `lumo`        | `Backend.Lumo`                   | Proton Lumo (U2L or proxy)           |
| `mock`        | `Backend.Mock`                   | tests                                |
| `claude_native` | `Backend.ClaudeCode`           | drives the `claude` CLI              |
| `cursor`      | `Backend.Cursor`                 | drives the `cursor` CLI              |

## Native CLI backends

`Backend.Native` drives a local coding-CLI as a backend; the CLI runs its own tool
loop (`handles_tools_internally?/0 == true`).

```elixir
defmodule Raxol.Agent.Backend.ClaudeCode do
  use Raxol.Agent.Backend.Native, driver: Raxol.Agent.Harness.ClaudeCode
end
```

The driver implements `Raxol.Agent.NativeHarness` (`executable/0`, `name/0`,
`args/1`, `parse_line/1`). `Harness.StreamJson` parses the NDJSON stream-json protocol;
`Harness.McpToolConfig` writes the MCP config that injects Raxol tools into the CLI.

## Backend.Mock (Testing)

```elixir
# Static
[response: "Hello"]

# Dynamic
[response_fn: fn -> "dynamic" end]

# Error
[error: :rate_limited]

# Tool calls
[tool_calls: [%{"name" => "read_file", "arguments" => %{"path" => "/tmp/x"}}]]

# Latency
[response: "slow", latency_ms: 200]
```

Always use Mock in tests. See `testing/agent-testing.md`.

## Usage in Process Agents

```elixir
Process.start_link(
  agent_id: :my_agent,
  agent_module: MyAgent,
  backend: Raxol.Agent.Backend.HTTP,
  backend_config: [provider: :anthropic, api_key: key, model: "claude-opus-4-6-20250415"]
)
```

The backend is passed to Strategy modules which handle the LLM loop.
