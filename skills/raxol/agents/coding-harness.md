---
title: Coding Harness (session engine + safety gates)
impact: CRITICAL
impactDescription: The durable session engine and safety substrate; a wrong gate or journal write-order can run a destructive tool or lose a session.
tags: raxol, agent, harness, journal, gates, coding-agent, safety
---

# Coding Harness (v2.6)

The Harness is Raxol's coding-agent engine: one durable, replayable agent
**session** plus a **safety substrate** of gates. It backs the product surfaces
`mix raxol.code` (interactive TUI), `mix raxol.p` (headless one-shot), and
`mix raxol.setup` (provider connect). Package split: the durable core + gates
live in `raxol_agent`; the projection/UI core lives in the root `raxol` package
and MUST never depend on `raxol_agent`.

Boundary: this is **one** agent session. `raxol-symphony` orchestrates *many*
tracker-driven runs above it (see `raxol-symphony` skill). Agentic-commerce spend
belongs to `raxol-payments` (`raxol_agent` does NOT depend on `raxol_payments` --
the dependency runs the other way; the SpendGate replicates the ledger's
reserve-before-call *shape*, it does not import it).

## The session engine: Contract -> Journal -> Projection -> Surface

```
producer (Stream.react / ToolExecutor / NativeHarness)
  └─ Raxol.Agent.Contract.pump/3      # emit typed events + assign turn_id/ids
       ├─ Raxol.Agent.SessionStreamer # live pub/sub -> surfaces subscribe
       └─ Raxol.Agent.Journal         # durable append-only, monotonic offset
Raxol.Harness.Projection.project/2    # journal fold -> ordered block list
  └─ Raxol.Harness.Surface            # init/update/render over a block model
```

Surfaces subscribe to the streamer / read the journal and render; **they never
reach into the loop**. Producers change, the contract does not.

### 1. Contract (the typed event boundary)

`Raxol.Agent.Contract` -- the typed core<->surface event contract (distinct from
`Raxol.Agent.Protocol`, which is agent-to-agent cockpit messaging).

```elixir
{:ok, result} = Raxol.Agent.Contract.pump(session_id, event_stream, prompt: "...")
```

`pump/3` consumes a producer's lazy event stream, assigns a turn-scoped
`turn_id` and per-item `item_id`s (`"i1"`, `"i2"`, ...), and emits the `:loop`
family vocabulary:

- `:turn_started` `%{prompt}`
- `:item_started` `%{item_id, item_type}` -- opened lazily at first non-blank delta
- `:item_delta` `%{item_id, chunk}` -- the **one ephemeral event** (live render
  only, never journaled/replayed)
- `:item_completed` `%{item_id, item_type: :message | :reasoning | :tool_use | :tool_result, ...}`
  -- `:reasoning` seals a durable, foldable chain-of-thought block
- `:turn_completed` `%{usage, iteration, final}` (`final: true` closes the run)
- `:error` `%{reason}`

The contract only **grows** (additive keys). A `turn_completed{final: true}` from
the DoneGate path also carries `evidence: :accepted | :rejected | :absent` plus
`refs`.

### 2. Journal (durable append-only tier)

`Raxol.Agent.Journal` is a behaviour; `Raxol.Agent.Journal.FileStore` is the
file-backed impl -- **one directory per session** (portable, tar/rsync/grep-able),
default `~/.raxol/sessions/` (`:base_dir` opt or `RAXOL_SESSIONS_DIR`).

```
<base>/<session_id>/
├── meta.json          # created_at, cwd, git branch, title, schema_version
├── HEAD               # current durable offset + config
├── journal/000001.jsonl   # framed JSONL, size-capped ascending segments
└── snapshots/
```

Callbacks: `open/2`, `append/2 -> {:ok, offset}`, `read/2`, `close/1`,
`status/1 :: :ok | :damaged`. Each event gets a monotonic `offset` (= its id) and
is framed one self-delimited JSON object per line. Split into a single-writer
`FileStore.Writer` and a tolerant replay `FileStore.Reader`.

**Durability law:** only *complete* records are returned. A parse failure on the
**last** line of the last segment is a torn tail (crash mid-write): truncated
away, everything before recovered, `status/1` stays `:ok`. A parse failure
**interior** marks `:damaged`, raises a hard alarm, deletes nothing, and never
returns the damaged content. Invariant I3: journal-before-publish -- append the
durable id, then publish; never publish an id ahead of its durable ack.

### 3. Reattach (offset replay / late subscriber)

`Raxol.Agent.Reattach.attach(session_id, from_offset, policy, opts)` gives a
(re)connecting client history + the live tail in one coherent stream with **no
gap and no duplicate delivered as live**:

```elixir
{:ok, %{history: _, from_offset: _, live: _}} =
  Raxol.Agent.Reattach.attach("sess-123", 0, :tip)
# history_policy :: {:from_offset, n} | :tip | :none
```

Replay-closure law: `read(0..o-1) ++ attach_live(o..) == full durable stream` as
a sequence; a late subscriber's first live id is `>= from_offset`. **Read-side
only** -- MUST work writerless (dead BEAM, replay-only mount, rsync'd dir); built
on the tolerant Reader, never the single-writer append path. `session_id` is a
path segment and is validated (`[A-Za-z0-9._-]+`, no `.`/`..`/NUL) before dispatch.

### 4. Projection + Surface (the render tier)

`Raxol.Harness.Projection.project/2` folds durable events into an ordered block
list; `item_delta` becomes live-tail state, never a durable block. It accepts a
loaded fixture session or a plain list of event-shaped maps (string-keyed
payloads, atom top-level fields). Recovery pipeline: id-monotonic filter
(drop duplicate/out-of-order; a forward gap soft-renders but sets `damaged?:
true`), partition `:loop` vs `:meta` (only `:loop` becomes blocks), bucket by
`turn_id`.

`Raxol.Harness.Surface` is the assembled `init/update/render` app over a block
model. It renders through a byte-level pinned-region substrate
(`PaintAuthority.InlineAuthority` -- DECSTBM scroll region + pinned footer), one
layer below the normal TEA pipeline, so it is deliberately NOT wired through
`Raxol.start_link/2`. Supporting projection modules:

- `Raxol.Harness.SealFrontier` -- the one classifier for which blocks may seal
  (commit to print-once scrollback) this frame vs. stay in the repaintable footer.
- `Raxol.Harness.PanelProjection` -- pure fold over `extract` meta events for the
  worktracks/memory/plan overlay panels.
- `Raxol.Harness.StreamCadence` -- decouples token ingest (network rate,
  unbounded, load-shed above `:max_pending`) from render egress (cadence-throttled);
  never backpressures the SSE producer.
- `Raxol.Harness.StallDetector` -- pure detection instrument that tells the human
  "the agent wedged" (stalled/looping) with an independent, non-refilling
  escalation budget; **never auto-recovers**.

### 5. Live wiring (the two seams)

- `Raxol.Harness.EventBoundary.normalize/1` -- the **security seam**. A live
  contract event crosses a process boundary (untrusted input). Normalizes atom-keyed
  live events into the fixture wire shape and enforces: no atom minting
  (`String.to_atom/1` never called), unknown fields dropped (only the 9 understood
  fields survive), taint never laundered (`provenance.trust` absorbs anything
  unrecognized to `:tainted`).
- `Raxol.Harness.LiveSessionDriver` -- a plain-process loop (NOT a GenServer, so a
  raw `receive ... after 0` can prioritize input over `{:render_batch, ...}`)
  supervising ONE live session: subscribe via an injected `Raxol.Harness.SessionLane`
  -> `EventBoundary.normalize` -> `StreamCadence` -> `Surface`, and back out through
  the lane's `:interrupt`/`:steer` dispatch. `Raxol.Agent.Harness.SessionLane` is the
  agent-side lane impl wiring the seam to the real `SessionStreamer` + `Command`.
- `Raxol.Harness.EditorSession` -- external `$EDITOR` handoff for the composer
  (Port with `:nouse_stdio` so the editor owns the real tty; OTP `user_drv` Ctrl+O
  mechanism).

## The tool-execution loop (live harness)

The framework-driven path (used when the backend does NOT own its own loop):

- `Raxol.Agent.Harness.SessionInbox` -- the GenServer session runtime. Consumes
  routed `{:harness_command, action}` messages, turns a `:prompt` into a
  tool-executing turn (one turn at a time; a mid-turn submit is queued to the next
  boundary). Owns **approvals**: before a consequential tool the executor calls
  `await_permission/3`, a `GenServer.call` that PARKS (stashing `from` keyed by
  `request_id`); the keyboard answer `{:approval_decision, _, %{request_id,
  option_id}}` maps to allow/deny and replies the parked caller. `pending` never
  outlives its turn.
- `Raxol.Agent.Harness.ToolExecutor` -- the tool loop: model emits a tool call ->
  executed (gated by approval where consequential) -> result fed back -> loop until
  a text-only answer. Drives with `complete/2`, not `stream/2` (the streaming path
  drops provider tool-call deltas), so a tool-bearing turn's text arrives per-round.
- `Raxol.Agent.Harness.ToolClassifier` -- the ONE place deciding consequential vs.
  auto-allowed, by tool **name**: `read_file/list_dir/file_stat/glob/grep`
  auto-allow; `write_file/edit_file/run_shell` consequential; **unknown =
  consequential (fail-closed)**. `sensitive:` (deny outright, fund-movers) is a
  different verdict from "ask first".

The vendor-owns-the-loop path (native CLI): `Raxol.Agent.NativeHarness` is the
driver behaviour (`executable/0`, `args/1`, `parse_line/1` -> normalized
`{:text|:reasoning|:tool_call|:done|:error}` tuples); `Backend.Native` handles
Port spawn/framing/exit. `Raxol.Agent.Harness.StreamJson` parses the
`--output-format stream-json` NDJSON shared by Claude Code + `cursor-agent`.
`Raxol.Agent.Harness.McpToolConfig` injects Raxol's Actions into the CLI as an MCP
server (`--mcp-config`), since the framework can't drive dispatch when the CLI owns
the loop. See `ai/backends.md` for harness/backend selection.

## The safety substrate (gates)

Gates are pure decision cores over the journal (the journal is the authority;
enforcement state is a projection rebuildable by a fold). Default posture is
**fail-closed**.

### BlastRadiusGate -- write/destructive LOCKED by default

`Raxol.Agent.Authorization.BlastRadiusGate` (U8). Write/destructive tools are
locked; a call is evaluated (`effect_class` + `egress` + taint) and either:

```elixir
{:proceeded, result, state} = ...   # standing approval covers it, or auto-approvable
{:escalated, request, state} = ...   # emits neutral approval_requested (family :loop) -- side effect does NOT run
{:rejected, reason, state}  = ...    # durable prior deny / hard reject -- side effect does NOT run
BlastRadiusGate.authorize(state, call, run_fn)
```

A decision arrives as an `approval_decided` meta event (`%{request_ref, decision,
refs}`); the actor lives on the **envelope only**, never the payload.
`rebuild/1` reconstructs identical enforcement state from the event log; the
approver is authenticated by the gate (fail-closed).

The broader authorization layer is `Raxol.Agent.Authorization.Engine` -- a pure
ALLOW/ASK/DENY reducer over ordered `Policy`s (DENY short-circuits; ALLOW merges
whitelisted label writes monotonically; ASK holds writes in escrow). `evaluate/5`
is pure; callers `commit/2` or `approve/2`. Approvals can be remembered per
`scope` (`:session` / `:root` per spawn tree). See the policy/hook layer in
[actions-pipelines.md](actions-pipelines.md).

### SpendGate -- reserve-before-call

`Raxol.Agent.SpendGate` (U7). Every spend-bearing call (LLM provider, paid tool)
journals `reserve -> call -> settle`, in that order, per call, correlated by an
opaque `cost_ref`.

```elixir
{:ok, reservation} = SpendGate.reserve(ctx, cost_ref, estimate)   # or {:error, {:refused, reason}}
{:ok, _settle}     = SpendGate.settle(ctx, reservation, actual)
# convenience wrapper:
{:ok, result} = SpendGate.around(ctx, cost_ref, estimate, fn -> {actual, do_call()} end)
#   or {:error, {:reserve_refused, reason}} -- call_fun NEVER invoked
```

Laws: **fail-closed** (no reserve => no call, ever; a refused reserve returns a
typed refusal); **settlement is internal** (`settle` records `actual`; the
`estimate - actual` refund is derivable from the pair). A `raise` in the call
releases the ETS claim so `cost_ref` is reclaimable, then re-raises. A real
journal-write failure raises `SpendGate.JournalWriteError` (charge + record must
not silently diverge); only a dead test bus is tolerated.

### DoneGate -- evidence-gated completion

`Raxol.Agent.DoneGate` (U21). An agent may not declare a turn done on its own
say-so: the `turn_completed{final: true}` transition is gated on journaled
evidence.

```elixir
DoneGate.gate(journal, turn_id, refs) ::
    {:ok, done_event}                       # turn_completed{final: true, refs: refs}
  | {:error, :unturned_done}                # nil turn (structural, checked first)
  | {:error, :evidence_required}            # no refs
  | {:error, {:missing_ref | :not_evidence | :foreign_turn | :stale_evidence | :mutation_echo, offset}}
```

`refs` are journal offsets, walked in order, first violation wins: each must
(1) resolve to a real record, (2) be evidence-class (a tool result / verification
output, never the agent's own `:message` or an internal `:state_change`), (3)
belong to the claiming turn, (4) strictly postdate the turn's last mutation, and
(5) not be the last mutation's own echo. **Every completed `:tool_use` is a
mutation** (fail-safe). Only then is the durable done event handed back, so a
surface can render "done because X".

### Steer -- redirect a running turn

`Raxol.Agent.Steer` (U6). *Inject at the next boundary* (vs. interrupt's *kill
now*). `resolve/2` is a **pure decision function**, not an atomic CAS -- it
returns a `{result, next_state}` on an `expected_turn_id` compare + `client_msg_id`
idempotency check. The runtime MUST serialize read-modify-write (exactly one owner
process holds the authoritative `TurnState`; a fetch->resolve->store cycle from
multiple processes is UNSOUND and can land two steers in one turn).

### Interrupt -- staged supervised kill

`Raxol.Agent.Interrupt.interrupt(tool_ref, sink, opts)` (U5). Not a polled flag: a
bounded escalation, each stage a durable event:

```
:interrupt_signaled  (cooperative group SIGTERM)
  -> :interrupt_waited   (grace window elapsed; default_grace_ms/0 is a policy knob)
  -> :interrupt_killed | :interrupt_kill_failed   (process-group SIGKILL; OS death confirmed out-of-band via ps)
  -> :turn_canceled      (terminal bracket, %{reason})
```

`:interrupt_killed` is emitted only when the whole process group's OS death is
confirmed (never by trusting `:exit_status`); otherwise `:interrupt_kill_failed`
is emitted in its place so the journal never claims a kill the OS didn't establish.

## Product surfaces (mix tasks)

- `mix raxol.code` -- interactive multi-turn coding TUI (the axol face `≡··≡`).
  Boots `Raxol.Agent.Code.App` (a TEA app, `use Raxol.Core.Runtime.Application`),
  a thin Lifecycle shell that drives the loop but reuses harness rendering
  (`Harness.Projection` + `UI.Components.Harness.Block`). On submit it spawns a
  worker that subscribes to a `SessionStreamer` session, runs `Stream.react/2`
  through `Contract.pump/3`, and relays each event back as
  `{:command_result, {:contract_event, event}}`, normalized via
  `EventBoundary.normalize/1`. Sensitive tools defer to a per-run
  `:tool_authorizer` -> `Authorization.Engine` (ALLOW / ASK once-always-deny /
  DENY). Keys: `a`/`s`/`d` approve, Shift+Tab plan mode, Esc deny/interrupt,
  Ctrl+C quit. Flags: `--continue`, `--resume <id>`, `--sessions`, `--backend`,
  `--model`, `--ascii`. Session store: `Raxol.Agent.Code.Store`; project config:
  `.raxol/hooks.json` (`Code.Hooks`) + `.mcp.json` (`Code.McpConfig`).
- `mix raxol.p "<prompt>"` -- headless one-shot (`raxol -p`). Boots the runtime
  (no UI), pumps a `Stream.react/2` run through `Contract` -- a real contract
  consumer. **stdout** = answer only (pipe-safe); **stderr** = every contract
  event as one JSON line (`2>events.jsonl` for a machine trace). Read-only fs
  tools by default; `--write` opts into `write_file/edit_file/bash` (sensitive,
  denied by default -- the flag installs an allow-all authorizer for the
  unattended run). Flags: `--backend`, `--model`, `--base-url`, `--system`,
  `--timeout`.
- `mix raxol.setup` -- headless provider connect/validate (non-TUI twin of
  `/login`). Writes only 1Password *references* to `~/.raxol/providers.json`
  (`$RAXOL_PROVIDERS`) via `Backend.{Credentials, Resolver}`, the front door every
  surface shares. Each connect validates with a token-free model-list call and
  exits non-zero on failure. Flags: `--provider`, `--op`, `--api-key`, `--model`,
  `--base-url`, `--vault`, `--remove`, `--status`.

## Pitfalls

1. **Publish-ahead of durable append** -- violates invariant I3; a late reattach
   sees an id the journal can't replay. Append (get offset) THEN publish.
2. **Reattach on the write path** -- reattach MUST work writerless; build on the
   tolerant Reader, never the single-writer Writer.
3. **Steer through shared storage from >1 process** -- unsound; `resolve/2` gives
   no atomicity. Only the single owner of `TurnState` may resolve+install.
4. **Trusting `:exit_status` for a kill** -- confirm process-group death
   out-of-band; otherwise emit `:interrupt_kill_failed`, never `:interrupt_killed`.
5. **Re-checking authorization inside `run/2`** -- gate at the boundary
   (`Authorization.Engine` / `BlastRadiusGate`), so every tool + MCP call shares
   one guardrail. Unknown tool names are consequential (fail-closed).
6. **Minting atoms from live events** -- always cross the process boundary through
   `EventBoundary.normalize/1`; never `String.to_atom/1` on producer-controlled
   strings.

## See also

- [tea-agent.md](tea-agent.md) -- `use Raxol.Agent`, the TEA loop the Code.App shell drives
- [actions-pipelines.md](actions-pipelines.md) -- Actions, LLM tool conversion, the policy/hook authorization layer
- [turn-memory.md](turn-memory.md) -- `Raxol.Agent.Turn`: a full LLM chat turn (memory + skills + tool loop)
- `ai/backends.md` -- AI backend + harness selection (HTTP / Native / Mock)
- `raxol-symphony` skill -- orchestrates many tracker-driven runs above one Harness session
- `raxol-payments` skill -- the ledger the SpendGate mirrors (reserve-before-call at the wallet boundary)
