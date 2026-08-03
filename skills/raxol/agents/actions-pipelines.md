---
title: Actions and Pipelines
impact: HIGH
impactDescription: Actions bridge agents to LLM tool use and must return correct types to avoid runtime crashes.
tags: raxol, agent, action, pipeline, tools
---

# Actions and Pipelines

Reusable, schema-validated operations that compose into pipelines and
auto-convert to LLM tool definitions.

## Defining an Action

```elixir
defmodule ReadFile do
  use Raxol.Agent.Action,
    name: "read_file",
    description: "Read a file from disk",
    schema: [
      input: [path: [type: :string, required: true, description: "File path"]],
      output: [content: [type: :string], line_count: [type: :integer]]
    ]

  @impl true
  def run(%{path: path}, _context) do
    case File.read(path) do
      {:ok, content} ->
        {:ok, %{content: content, line_count: length(String.split(content, "\n"))}}
      {:error, reason} ->
        {:error, {:file_read_failed, reason}}
    end
  end
end
```

Schema types: `:string`, `:integer`, `:boolean`, `:map`, `:list`.
Field opts: `:required`, `:description`, `:default`.

## Callbacks

```elixir
@callback run(params :: map(), context :: map()) ::
  {:ok, map()} | {:ok, map(), [Command.t()]} | {:error, term()}

# Optional
@callback before_validate(params()) :: params()   # transform before validation
@callback after_run(map(), context()) :: map()     # transform after success
```

INCORRECT:

```elixir
def run(%{path: path}, _), do: File.read!(path)  # must return {:ok, map()}
```

CORRECT:

```elixir
def run(%{path: path}, _), do: {:ok, %{content: File.read!(path)}}
```

## Calling Actions

```elixir
# Direct (outside agent)
{:ok, result} = ReadFile.call(%{path: "/tmp/x"})

# From TEA agent (see SKILL.md for result message formats)
run_action(ReadFile, %{path: "/tmp/x"})        # sync, blocks update/2
run_action_async(ReadFile, %{path: "/tmp/x"})   # async command
run_pipeline_async([Step1, Step2], params)       # sequential pipeline
```

## Pipelines

Each step's output merges into shared state. Stops on first error.

```elixir
{:ok, result, commands} = Raxol.Agent.Action.Pipeline.run(
  [FetchData, ProcessData, SaveResult], initial_params, context
)
# Error: {:error, {FailedStepModule, reason}}
```

## LLM Tool Conversion

Actions auto-generate JSON Schema for LLM tool use:

```elixir
alias Raxol.Agent.Action.ToolConverter

tools = ToolConverter.to_tool_definitions([ReadFile, WriteFile])
{:ok, result} = ToolConverter.dispatch_tool_call(llm_tool_call, actions, ctx)
formatted = ToolConverter.format_tool_result(tool_call, result)
```

Process agents expose actions via `available_actions/0`. When a Strategy
(e.g., `Strategy.ReAct`) is configured, returning `{:act, {ActionModule, params}, state}`
from `think/2` runs the LLM tool loop automatically.

## Shipped action families (`Raxol.Agent.Actions.*`)

Ready-made action modules under `packages/raxol_agent/lib/raxol/agent/actions/`.
Each family exposes `actions/0` returning its Action modules to pass as `actions:`
to a ReAct run (or add to `available_actions/0`). Tool names in parentheses.

| Family                 | Module                          | Tools                                                          | Notes |
| ---------------------- | ------------------------------- | ------------------------------------------------------------- | ----- |
| **Code** (mutating)    | `Actions.Code`                  | `write_file`, `edit_file`, `bash`, `grep`, `glob`             | Real cwd-scoped FS. `write_file`/`edit_file`/`bash` are `sensitive: true`. `Code.all/0`, `Code.read_only/0` (grep+glob). |
| **Fs** (read-only)     | `Actions.Fs`                    | `list_dir`, `read_file`, `file_stat`                          | Real FS, strictly read-only. Path containment via `Fs.resolve/1` on the REALPATH (symlink-safe). |
| **Workspace**          | `Actions.Workspace`             | `write_file`, `edit_file`, `glob`, `grep`                     | Mutating + search. NOT `sensitive` -- consequentiality is a harness ASK-gate decision, not an Action flag. |
| **Shell**              | `Actions.Shell`                 | `run_shell`                                                   | Single consequential `/bin/sh -c` Port. Interruptible + staged-kill on ESC/timeout (see `Interrupt` below). |
| **Task** (delegate)    | `Actions.Task`                  | `task`                                                        | Spawns a fresh READ-ONLY sub-agent (`Stream.react/2`) -- no write/bash/task tools, cannot recurse. Backend from `context[:subagent]`. |
| **Vfs** (in-memory)    | `Actions.Vfs`                   | `vfs_list_dir`, `vfs_read_file`, `vfs_write_file`, `vfs_make_dir`, `vfs_change_dir`, `vfs_remove`, `vfs_get_tree` | Virtual FS in agent model; state via `context[:vfs]`, mutations return updated `:vfs`. |
| **Cronjob**            | `Actions.Cronjob`               | `cronjob` (create/list/update/pause/resume/run/remove)       | Over `Raxol.Agent.Scheduler` via `context[:scheduler]`. Owner-scoped; `in_cron: true` guard blocks scheduling from a fired job. |
| **Memory**             | `Actions.Memory`                | `memory_remember`, `memory_recall`, `memory_forget`          | Cross-session memory via `context[:memory]`. See [turn-memory.md](turn-memory.md). |
| **SessionSearch**      | `Actions.SessionSearch`         | `session_search`                                             | Search raw prior conversation messages/tool results via `context[:session_search]`. |
| **Skills**             | `Actions.Skills`                | `skills_list`, `skill_view`, `skill_manage` (create/update/delete) | Procedural memory via `context[:skills]`. See [skills-procedural-memory.md](skills-procedural-memory.md). |

Each family reaches its dependency through a `context[:*]` key (`:vfs`, `:memory`,
`:skills`, `:scheduler`, `:session_search`, `:subagent`), injected by the surface
running the loop. `use Raxol.Agent` wires Memory/Skills into `available_actions/0`
automatically when a provider is configured.

## Authorization & gating (v2.6)

Two layers gate tool/action execution before it runs. Configure them on the agent
or in the run context -- never re-check inside `run/2`, so the same guardrails
apply to every action and MCP tool call.

**1. Tool-call authorizer (`Raxol.Agent.ToolPolicy`).** A
`(action_module, params, context) -> :ok | {:deny, reason}` fun placed under
`context[:tool_authorizer]`. `ToolConverter.dispatch_tool_call/3` consults it
before invoking the Action, so a prompt-injected LLM cannot drive a sensitive
tool by emitting a tool call. Combinators: `deny_sensitive/0` (default: denies any
Action marked `sensitive: true`), `allow_all/0`, `allowlist/1`, `denylist/1`,
`all/1` (deny if any denies). Absent, calls are allowed (backward compatible).

**2. Phase-aware policy engine (`Raxol.Agent.Authorization.Engine`).** A pure
ALLOW/ASK/DENY reducer over an ordered `Policy` list at a phase (e.g. `:tool_call`).
DENY short-circuits (keeps prior ALLOW label writes); ALLOW merges its whitelisted
label writes monotonically; ASK accumulates an approval request and holds writes in
ESCROW until approved. Final action = DENY if any denied, else ASK if any asked,
else ALLOW. `evaluate/5` is pure; callers `commit/2` an ALLOW/DENY or `approve/2`
an ASK. Approval memory is scoped `:session` or `:root` (a spawn-tree root `route`
scoped `:root` makes one approval cover the whole tree). Returns a `Verdict`.

### The harness safety gates

The deep enforcement gates live in the coding harness -- documented in depth in
[coding-harness.md](coding-harness.md). Summary of the seams:

- **`Authorization.BlastRadiusGate`** (U8) -- write/destructive tools are **LOCKED
  by default**. `authorize/3` either proceeds (standing/auto-approval over trusted
  lineage), escalates (returns an `approval_requested` neutral event; side effect
  does NOT run), or rejects. A decision arrives as an `approval_decided` meta event
  and is enacted **only** when the envelope actor is `%{kind: :human}` (fail-closed).
  Live approval state is a projection rebuildable by folding `approval_decided`
  events (`rebuild/1`).
- **`SpendGate`** (U7) -- reserve-before-call at the tool/provider boundary. Every
  spend-bearing call journals `reserve -> call -> settle` per call, correlated by an
  opaque `cost_ref`. Fail-closed: no reserve => no call, ever. Mirrors the payments
  stack's `try_spend` shape without importing it (raxol_agent does not depend on
  raxol_payments).
- **`DoneGate`** (U21) -- evidence-gated done. An agent may not declare a turn done
  on its own say-so; a `turn_completed{final: true}` is gated on journaled evidence
  (tool results / verification outputs) that postdates the turn's last mutating
  action. Pure read/decision over the turn journal; refs must exist, be
  evidence-class, belong to the claiming turn, postdate the last mutation, and not be
  that mutation's own echo.
- **`Steer`** (U6) -- redirect a running turn with new user input WITHOUT killing it
  (inject at the next boundary). Pure `expected_turn_id` CAS *decision* +
  `client_msg_id` idempotency; the runtime must serialize read-modify-write through
  the turn's single owner process for the concurrent-steer guarantee to hold.
- **`Interrupt`** (U5) -- staged supervised kill: `interrupt_signaled` (cooperative
  SIGTERM) -> `interrupt_waited` (bounded grace) -> `interrupt_killed` (process-group
  SIGKILL, confirmed out-of-band via `ps`). Each stage is a durable event. The
  `Shell` `run_shell` tool wires into this on ESC and on wall-clock timeout so a
  timed-out command's OS process group is killed, not just the BEAM port closed.
