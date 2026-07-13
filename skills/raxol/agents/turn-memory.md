---
title: Turn Driver, Memory + Self-Improvement
impact: HIGH
impactDescription: Skipping the turn driver means re-implementing memory recall, session search, and after-turn effects by hand.
tags: raxol, agent, turn, memory, skills, self-improve
---

# Turn Driver, Memory + Self-Improvement (v2.6)

`Raxol.Agent.Turn` is the driver for a full LLM chat turn: it assembles context
(memory, skills, user model, session search), runs the tool loop against a backend,
records to the conversation log, and fires after-turn effects (curation,
self-improvement). Package: `packages/raxol_agent`.

## Run a turn

```elixir
{:ok, output} =
  Raxol.Agent.Turn.run(MyAgent, "summarize the repo",
    backend: Raxol.Agent.Backend.HTTP,
    backend_opts: [provider: :anthropic, model: "claude-sonnet-4-6"],
    log: conversation_log,
    conversation_id: "conv-1",
    user_id: "u-42",
    memory_opts: [provider: Raxol.Agent.Memory.Store.Ets],
    skills_opts: [root: "priv/skills"],
    max_iterations: 8
  )
```

`build_context/2` (memory + skills + user_context + session_search) and
`after_turn/4` are exposed if you drive the loop yourself.

## Memory stack

`Raxol.Agent.Memory` is a behaviour (`search/2`, `store/2`, `forget/2`).
`Memory.Stack` composes N providers -- fan-out writes, merge+rerank reads.

```elixir
# Compose providers; reads dedupe + rank across all
memory = [
  {Raxol.Agent.Memory.Store.Ets, table: :agent_mem},
  {Raxol.Agent.UserModel, server: MyUserModel}
]

Raxol.Agent.Memory.Stack.store(record, providers: memory)
records = Raxol.Agent.Memory.Stack.search("deploy step", providers: memory)
block   = Raxol.Agent.Memory.format_block(records)  # -> String injected into prompt
```

`Raxol.Agent.Memory.SessionSearch` is a GenServer BM25-lite inverted index over raw
conversation items: `start_link/1`, `index/2`, `attach/3`, `search/3`.

## Self-improving skills

Skills use the agentskills.io `SKILL.md` format. `Raxol.Agent.Skill` parses/renders;
`Raxol.Agent.Skills.Store` is a disk-backed index with usage telemetry.

```elixir
{:ok, store} = Raxol.Agent.Skills.Store.start_link(root: "priv/skills")
{:ok, skill} = Raxol.Agent.Skill.from_file("priv/skills/deploy/SKILL.md")
skills       = Raxol.Agent.Skills.Store.list(store)
{:ok, body}  = Raxol.Agent.Skills.Store.view(store, "deploy", nil, [])
:ok          = Raxol.Agent.Skills.Store.record_use(store, "deploy", [])
```

`Raxol.Agent.Curator` ages skills `active -> stale -> archived` (interval + idle
gating, with backup/`rollback/1`). `Raxol.Agent.SelfImprove.after_turn/3` spawns an
isolated, unlinked reviewer that writes durable memory + skills after qualifying turns
(`qualifies?/2`).

## User model + auxiliary routing

`Raxol.Agent.UserModel` derives a per-user dialectic block on an auxiliary model and
injects it into the last user message. `Raxol.Agent.Auxiliary.resolve/2` routes
background tasks (curation, user-model refresh, session summary) to a cheaper model
per task kind.

```elixir
{:ok, um} = Raxol.Agent.UserModel.start_link(name: MyUserModel)
Raxol.Agent.UserModel.refresh_async(um, "u-42", conversation_items, [])
ctx = Raxol.Agent.UserModel.get_context(um, "u-42")   # dialectic block or nil

cfg = Raxol.Agent.Auxiliary.resolve(:curation, [])     # -> ExecutorConfig for a cheap model
```

## Pitfalls

1. **Passing a bare string when history is expected** -- `Turn.run/3` accepts a
   prompt string or a list of message maps; mixing shapes drops prior turns.
2. **Self-improve linked to the caller** -- `SelfImprove` runs unlinked on purpose;
   don't `link` it or a reviewer crash takes down the agent.
3. **UserModel on the main model** -- route it through `Auxiliary` to a cheap model;
   refreshing the dialectic block on the primary model is wasteful.
