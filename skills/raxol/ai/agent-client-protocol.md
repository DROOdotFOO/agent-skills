---
title: Agent Client Protocol (Bridge)
impact: MEDIUM
impactDescription: Editor-integration protocol; only needed when exposing a Raxol agent to a code editor over ACP, but the name collision with raxol_acp is a correctness trap.
tags: raxol, agent, acp, client-protocol, editor, jsonrpc
---

# Agent Client Protocol (`raxol_agent_client_protocol`)

## NAME COLLISION -- read this first

Two DIFFERENT "ACP"s live in the Raxol monorepo. They share three letters and
NOTHING else. Pick the wrong one and every symbol you reach for is wrong.

| Package                          | "ACP" means                | Domain                                              | Skill            |
| -------------------------------- | -------------------------- | -------------------------------------------------- | ---------------- |
| `raxol_agent_client_protocol`    | Agent **CLIENT** Protocol  | editor <-> agent JSON-RPC (Zed et al.), THIS file  | `raxol` (here)   |
| `raxol_acp`                      | Agent **COMMERCE** Protocol| Virtuals / on-chain payments / job sessions        | `raxol-payments` |

- Module roots: `Raxol.AgentClientProtocol.*` (this) vs `Raxol.ACP.*` (payments).
- If you are wiring an editor to drive a coding agent -> this file.
- If you are doing agent wallets, x402/402 auto-pay, or ACP job offerings ->
  the `raxol-payments` skill. Do not document or reach into `Raxol.ACP.*` here.

The package's own README opens with the same disambiguation. When in doubt,
check the module prefix, not the acronym.

## What it is

Elixir/OTP implementation of [ACP](https://agentclientprotocol.com) -- the
JSON-RPC 2.0 protocol a code editor (the **client**/host: Zed, an IDE, a CLI)
speaks to an AI coding **agent** it launched as a subprocess. Same shape as
LSP, but for agentic coding sessions instead of language tooling.

- Status: pre-alpha (`0.1.0-rc.0`), not on Hex.
- Zero raxol-internal deps -- a leaf package depending only on `jason`. The
  agent framework depends on IT, never the reverse (see integration below).
- Implements BOTH roles behind one `Connection` core, because ACP is
  bidirectional: mid-turn the agent becomes the caller
  (`session/request_permission`, `fs/*`, `terminal/*` requests TO the client).

Method families: `initialize` (handshake / capability negotiation), `session/*`
(`new`, `load`, `prompt`, `update`, `request_permission`, `cancel`), `fs/*`
(`read_text_file`, `write_text_file`), `terminal/*`.

## Module layers

```
Raxol.AgentClientProtocol
|- Schema.*        # ACP v1 wire data model; total decode, never String.to_atom on wire input
|- Rpc.*           # JSON-RPC 2.0 envelope; id correlation (null|int|string, type-preserving)
|- Transport.*     # pluggable byte/message carriers (Stdio, Paired, Framer)
|- Connection      # one GenServer per peer, either role, request correlation
|- Session         # per-session turn state machine (agent role), under DynamicSupervisor
|- Agent / Client  # use-able behaviours, callbacks generated from MethodTable
|- MethodTable / Router  # single source of truth for wire vocab + compile-time dispatch
|- Ext.*           # vendor extension: durable resumable sessions
```

Key invariants worth knowing when you build on it:

- **Total decode.** Malformed/unknown wire input never crashes and never mints
  an atom; decoders return `{:ok, struct} | {:error, reason}` or a best-effort
  struct with a raw fallback.
- **Connection never blocks on a peer.** Every inbound request/notification
  dispatches to a `Task.Supervisor.async_nolink` task; handler code never runs
  in the Connection's own process. Method->callback mapping is compile-time
  `Router`/`MethodTable` clauses only (the G2 gate).
- **Generated callback surface.** `Agent`/`Client` `@callback`s derive from
  `MethodTable.rows_for_side/1` at compile time, so they cannot drift from the
  wire vocabulary. Override only the callbacks your role implements; the rest
  default to `{:error, Error.method_not_found()}` (requests) or silent `:ok`
  (notifications).

## Transports

Behind one `Transport` behaviour:

- `Transport.Stdio` -- newline-delimited JSON-RPC over real or spawned stdio,
  single-writer serialized. The stock ACP wire. `start_self/0` adopts this
  BEAM's own stdin/stdout; `start_spawn/2` launches a subprocess agent.
- `Transport.Paired` -- `create_pair/0` returns two linked in-process handles.
  The test backbone, also for BEAM-local agent<->client wiring with no
  subprocess.
- `Transport.Framer` -- shared byte-splitting (partial-buffer, CRLF tolerance,
  oversized-line bounds) for stdio-shaped transports.

`transport:` opts take a `{module, handle}` pair, NOT the bare handle
`start_self/1` returns.

## Minimal agent (stdio)

```elixir
defmodule MyAgent do
  use Raxol.AgentClientProtocol.Agent
  alias Raxol.AgentClientProtocol.Connection
  alias Raxol.AgentClientProtocol.Schema.{ContentChunk, TextContent}
  alias Raxol.AgentClientProtocol.Schema.LifecycleExtras.SessionNotification
  alias Raxol.AgentClientProtocol.Schema.AgentTypes.{
    InitializeResponse, NewSessionResponse, PromptResponse
  }

  @impl true
  def initialize(req, _ctx), do: {:ok, InitializeResponse.new(req.protocol_version)}

  @impl true
  def new_session(_params, _ctx), do: {:ok, NewSessionResponse.new("sess-1")}

  @impl true
  def prompt(%{session_id: sid, prompt: blocks}, ctx) do
    text = Enum.map_join(blocks, "", fn {:text, tc} -> tc.text; _ -> "" end)
    chunk = ContentChunk.new({:text, TextContent.new("echo: #{text}")})
    Connection.notify(ctx.conn, "session/update", SessionNotification.new(sid, {:agent_message_chunk, chunk}))
    {:ok, PromptResponse.new(:end_turn)}
  end
end

# Boot: adopt this BEAM's stdio as the wire, run under --no-halt.
{:ok, handle} = Raxol.AgentClientProtocol.Transport.Stdio.start_self()
{:ok, _sup} = Raxol.AgentClientProtocol.Agent.start_link(MyAgent,
  transport: {Raxol.AgentClientProtocol.Transport.Stdio, handle})
```

The mandatory client-side sequence: `initialize` -> `session/new`
(or `session/load` to resume) -> one or more `Client.prompt/2` turns.
`Client.start_link/2` / `Agent.start_link/2` return the `ConnectionSupervisor`;
resolve the Connection pid with `Client.connection/1` before issuing requests.

## Durable resumable sessions (`Ext.*`)

Stock ACP session state is process-local -- kill the agent, lose the turn. The
`Ext.*` vendor extension (`_meta["raxol.io"]` rider on `session/load` /
`session/update`, plus new `_raxol/*` methods) makes a session durable and
reattachable across connections and processes:

- **Append-only journal, single publisher** per `session_id`
  (`Ext.Journal.Writer`): append-then-publish, no publish-ahead.
- **Offset-based reattach, no gap / no dup**: `Reattach.attach/1` registers as
  a live subscriber FIRST, then reads high watermark `h`, replays `(from..h]`
  as wire frames, then responds carrying `h`. Register-before-`h` is the whole
  correctness argument (the G5 gate).
- **Ed25519 offline capability tokens** (`RXC1`): authorize an attach to a
  writerless (tarred, offline) journal from token bytes + a public key alone;
  no `alg` field, so JWT-style downgrade confusion is structurally impossible.
- **Taint: annotate, never filter** -- records carry taint but no code path
  drops/reroutes by it; the only filtering axis is *kind*, keeping
  `history ++ live == the durable stream` an invariant.

Opt-in, not turnkey. `use Agent` alone returns `method_not_found` on the
`_meta["raxol.io"]` rider and `_raxol/session.load`. To enable: (1) splice
`RaxolAgentClientProtocol.Application.children()` into your supervisor once at
app level; (2) implement `new_session/2` to open a journal + start a durable
`Session`, and `raxol_load_session/2` to route through `Reattach.attach/1`.
Today's store `Ext.Journal.Mem` is in-memory (durable across connections within
one node, not across restarts); a disk-backed store must satisfy the G6 gate
(`0600`/`0700` modes) before it ships.

## Integration into the Raxol agent runtime

Two modules in `raxol_agent` (NOT in the protocol package -- the runner reaches
ACROSS to the leaf package, guarded by `Code.ensure_loaded?/1` + a dev/test
path dep, so production embedders opt in by adding
`:raxol_agent_client_protocol` themselves):

### `Raxol.Agent.ClientProtocol.TurnRunner`

The production `:turn_runner` for `Raxol.AgentClientProtocol.Session`. Wraps the
real streaming stack (`Raxol.Agent.Stream.run/2` / `react/2`, backend via
`Raxol.Agent.Backend.Selector` per `ExecutorConfig`) and posts each stream event
into the ACP session via `Raxol.AgentClientProtocol.Ctx.post_update/2`:

- `{:text_delta, t}` -> `agent_message_chunk`
- `{:tool_use, tu}` -> `tool_call` (`:in_progress`, `raw_input`)
- `{:tool_result, tr}` -> `tool_call_update` (`:completed`/`:failed`, `raw_output`)
- `{:done, _}` -> `{:stop, :end_turn}` (Session renders the one `PromptResponse`)
- `{:error, reason}` -> internal-error `session/prompt` response

```elixir
runner = Raxol.Agent.ClientProtocol.TurnRunner.new(
  executor: Raxol.Agent.ClientProtocol.TurnRunner.detect_executor(),  # env-driven, explicit
  system_prompt: "..."  # binary or a SystemPrompt source spec (resolved at wiring time)
)
# runner :: (session_pid, prompt_req) -> {:stop, _}; pass as Session :turn_runner
```

`new/1` fails LOUD at wiring time (not mid-turn) if the package is absent or a
`:system_prompt` source fails to resolve. Cancellation is Interrupt-law-correct:
the backend stream is consumed by a linked pump process so `:acp_cancel` is seen
mid-chunk even against a hung backend; on cancel the pump is killed and queued
events flushed BEFORE `Raxol.Agent.Interrupt.interrupt/3` runs the staged
OS-pgroup kill; a kill-fence rides the `SessionNotification` `_meta` under
`"raxol.dev/interrupt"` (`fence_meta_key/0`), then `{:stop, :cancelled}` lets the
Session render exactly one cancelled `PromptResponse`.

### `Raxol.Agent.AcpStreamAdapter`

The reverse direction: consumes decoded `session/update` frames (from
`Client.subscribe/3`, delivered as `{:acp_session_update, session_id, update}`)
and re-emits them as `Raxol.Agent.Contract.Event`s through
`Raxol.Agent.SessionStreamer` -- the same channel `Contract.pump/3` and
`EmitBridge` publish on. Any surface already subscribed to the streamer (live
driver, CLI, SSE) renders an ACP-backed session unchanged.

```elixir
{:ok, adapter} = Raxol.Agent.AcpStreamAdapter.start_link(
  session_id: "sess-1",
  subscribe: {conn, "sess-1"}  # requires the ACP package; else {:error, :acp_client_unavailable}
)
{:ok, turn_id} = Raxol.Agent.AcpStreamAdapter.begin_turn(adapter, prompt)
:ok = Raxol.Agent.AcpStreamAdapter.finish_turn(adapter, prompt_response_or_error)
```

Mapping is honesty-preserving: `begin_turn/2` emits `:turn_started` then a
durable user-echo `:message` item (empty prompt -> no echo);
`agent_message_chunk`s accumulate and seal as one durable `:message` at
`finish_turn/2`; `agent_thought_chunk`s drive a `:reasoning` item lifecycle;
`tool_call`/`tool_call_update` emit only at terminal status. Stop reasons are
never laundered -- `:cancelled` -> `:turn_canceled`, `:refusal` discloses
`refused: true`, an out-of-enum reason -> `:unknown` with `raw_stop_reason`.
Unmapped update variants are skipped, counted (`unmapped_counts/1`), and the
first of each kind emits one durable `:error` event.

## Testing

```bash
cd packages/raxol_agent_client_protocol && MIX_ENV=test mix test
mix acp.schema.verify   # official ACP JSON Schema oracle drift gate (schema-v1.19.0, dev/test only)
```

Three conformance nets: the ported MIT `acpx` case corpus
(`test/conformance/`), the schema oracle, and `test/torture/` (adversarial wire
fuzzing + P-BUS invariant coverage). For BEAM-local tests swap `Transport.Stdio`
for `Transport.Paired.create_pair/0`.

## See also

- `ai/backends.md` -- the LLM backends `TurnRunner` drives per `ExecutorConfig`.
- `ai/mcp-client.md` -- consuming external MCP tool servers (a different
  protocol; ACP is editor-integration, MCP is tool-provisioning).
- `raxol-payments` skill -- the OTHER "ACP" (`Raxol.ACP.*`, Agent Commerce
  Protocol). Not this package.
