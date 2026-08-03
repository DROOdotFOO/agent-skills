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

## ExecutorConfig + Backend.Selector

`Raxol.Agent.ExecutorConfig` is the declarative front door: a struct of
`{backend, model, auth, opts}` that replaces `Backend.HTTP`'s implicit `base_url`
substring detection. `:backend` is canonical; `:harness` is a deprecated alias.

```elixir
cfg = ExecutorConfig.new(backend: :anthropic, model: "claude-opus-4-8")
cfg = ExecutorConfig.new(backend: :openai, model: "gpt-5", auth: %{api_key: "sk-x"})
ExecutorConfig.to_backend_opts(cfg)  # flatten to backend keyword opts
```

`Raxol.Agent.Backend.Selector.select/1` resolves an `ExecutorConfig` to
`{:ok, backend_module, backend_opts}` (defaults merged with the config's flattened
model/auth/opts; config wins on conflict). `Selector.supported_backends/0` lists the
resolvable atoms. Backend atom -> module:

| Backend         | Module (+ defaults)                        | Notes                             |
| --------------- | ------------------------------------------ | --------------------------------- |
| `anthropic`     | `Backend.HTTP` (`provider: :anthropic`)    |                                   |
| `openai`        | `Backend.HTTP` (`provider: :openai`)       |                                   |
| `kimi`          | `Backend.HTTP` (`provider: :kimi`)         |                                   |
| `ollama`        | `Backend.HTTP` (`provider: :ollama`)       | local                             |
| `lm_studio`     | `Backend.HTTP` (openai, localhost:1234)    | local; placeholder `lm-studio` key |
| `llm7`          | `Backend.HTTP` (openai, api.llm7.io)       | free, no key                      |
| `longcat`       | `Backend.HTTP` (openai, api.longcat.chat)  | Meituan; default `LongCat-2.0`    |
| `openrouter`    | `Backend.HTTP` (openai, openrouter.ai/api) | adds `HTTP-Referer`/`X-OpenRouter-*` |
| `lumo`          | `Backend.Lumo`                             | Proton Lumo (U2L or proxy)        |
| `mock`          | `Backend.Mock`                             | tests                             |
| `claude_native` | `Backend.ClaudeCode`                       | drives the `claude` CLI           |
| `cursor`        | `Backend.Cursor`                           | drives the `cursor` CLI           |

`:codex` is reserved and returns `{:error, {:backend_not_implemented, :codex}}` (it
speaks a stateful JSON-RPC `app-server` protocol served by Symphony, not a backend
here). Unknown atoms return `{:error, {:unknown_backend, backend}}`.

## Backend.Resolver (provider / key / model)

`Raxol.Agent.Backend.Resolver.resolve/1` is the single source of truth for "which
provider, which key, which model", producing a ready `ExecutorConfig`. Every agent
surface (coding TUI, agent framework, MCP/headless default) resolves here so onboarding
has one shape.

```elixir
case Resolver.resolve(harness: :anthropic, model: "claude-opus-4-8") do
  {:ok, config, source} -> Selector.select(config)  # source :: :explicit | :op | :env | ...
  {:no_key, harness}    -> prompt_for_login(harness) # named but no credential resolved
  :no_provider          -> show_setup_panel()        # nothing detected -> honest signal
end
```

Recognized opts: `:harness` (atom or string), `:api_key`, `:model`, `:base_url`.

- Explicit harness -- key precedence: `:api_key` opt > 1Password ref (`Credentials` or
  `RAXOL_<HARNESS>_OP`, read via `op`) > provider env var(s)
  (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, ...). Model precedence: `:model` opt > stored
  entry > provider `*_MODEL` env var.
- No harness -- auto-detect walks the provider registry top-to-bottom (hosted/keyed
  before local; a keyless provider is only auto-selected when a reference is stored for
  it), then the generic `AI_API_KEY`/`AI_BASE_URL`/`AI_MODEL` trio (mapped onto
  `:openai`), then `:no_provider`.

Also: `Resolver.status/0` and `diagnostics/0` for the setup panel / `/login`
(per-provider `available?` + actionable `note`), `providers/0`, and
`harness_from_string/1` (maps a string to a known atom without minting new atoms).

## Backend.Credentials (1Password-first)

`Raxol.Agent.Backend.Credentials` stores only *references*, never raw keys: a
`~/.raxol/providers.json` map (`$RAXOL_PROVIDERS` override, `0600`) tying a provider
harness to a `op://...` reference plus optional `model` / `base_url`. Resolving shells
out to `op read` at launch, so no plaintext key touches disk.

```json
{ "anthropic": {"op_ref": "op://Employee/Anthropic/api_key", "model": "claude-sonnet-5"},
  "openai":    {"op_ref": "op://Employee/OpenAI/api_key"} }
```

```elixir
Credentials.fetch(:anthropic)            # {:ok, %{op_ref: ..., model: ...}} | :none
Credentials.put(:openai, op_ref: "op://Employee/OpenAI/api_key")  # :ok (0600 write)
Credentials.read_ref("op://...")         # {:ok, secret} | {:error, reason}
Credentials.create_item(:anthropic, key) # -> {:ok, "op://..."} (temp 0600 template)
Credentials.op_status()                  # :absent | :not_signed_in | :ok
```

Only `op_ref` / `model` / `base_url` round-trip; a malformed file yields `%{}` (never
crashes boot). `create_item/3` writes the vault named by `$RAXOL_OP_VAULT` (default
`Private`) and passes the secret via `--template`, never on argv. A raw key supplied per
session (env var, or `/login`) stays in memory only.

## Backend.Cli (`--backend` / `--harness`)

`Raxol.Agent.Backend.Cli.resolve(opts, prog)` is the shared `--backend` / `--harness`
flag handler for the `raxol.code` and `raxol.p` mix tasks, so the two cannot drift.
`--backend` is canonical; `--harness` is a deprecated alias (backend wins if both are
given). Returns `{:ok, backend_atom}` (validated against `Selector.supported_backends/0`)
or `{:error, message}` for an unknown name. Default backend is `lm_studio`. Pass
`prog: nil` to suppress the stderr deprecation notice -- `raxol.p` reserves stderr for
its JSONL event stream, so a plain-text line would corrupt it.

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
  backend_config: [provider: :anthropic, api_key: key, model: "claude-opus-4-8"]
)
```

The backend is passed to Strategy modules which handle the LLM loop.
