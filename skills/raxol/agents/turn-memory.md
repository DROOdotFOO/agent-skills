---
title: Turn Driver, Memory + Session Search
impact: HIGH
impactDescription: Skipping the turn driver means re-implementing memory recall, session search, user modeling, and after-turn effects by hand.
tags: raxol, agent, turn, memory, session-search, user-model
---

# Turn Driver, Memory + Session Search (v2.6)

`Raxol.Agent.Turn` is the driver for a full LLM chat turn: it assembles context
(memory, skills, user model, session search), runs the tool loop against a backend,
records to the conversation log, and fires after-turn effects (curation,
self-improvement). Package: `packages/raxol_agent`.

For the procedural-memory / self-improving-skills half of the after-turn write path
(`Skills.Store`, `Curator`, `SelfImprove`), see
[skills-procedural-memory.md](skills-procedural-memory.md). This file covers the
semantic memory + session-search half.

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
    skills_opts: [server: :my_skill_store],
    max_iterations: 8
  )
```

`build_context/2` (memory + skills + user_context + session_search) and
`after_turn/4` are exposed if you drive the loop yourself.

## Memory stack

`Raxol.Agent.Memory` is a behaviour. Mandatory callbacks: `search/2`, `store/2`,
`forget/2`; `prefetch/2`, `build_system_prompt/1`, and `build_user_context/1` have
defaults from `use Raxol.Agent.Memory`. `opts` carry `:server`, `:agent_id`
(partition), `:limit` (default 5), `:query`, `:query_tags`, `:tags`.

Providers under `packages/raxol_agent/lib/raxol/agent/memory/`:

- `Memory.Store.Ets` -- the concrete store (ETS inverted index, `start_link/1`,
  `search/2`, `store/2`, `forget/2`). This is the default `:memory_provider`.
- `Memory.Stack` -- composes N providers: fan-out writes, merge+rerank reads.
- `Memory.SessionSearch` -- BM25-lite index over raw conversation items (below).
- `Memory.Manager` -- pure helpers that weave a `{module, opts}` provider into a
  turn: `enrich_messages/3` prefetches relevant memories and injects them as a
  system message after any static system prefix (failures degrade to a no-op).
- `Memory.Record` -- the entry struct: `id`, `agent_id`, `content`, `type`
  (`:decision | :pattern | :gotcha | :link | :insight | :note`), `tags`,
  timestamps, `score`. `Record.tokenize/1` is shared by writer and searcher.

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

Build the normalized `context[:memory]` tuple with
`Raxol.Agent.Memory.provider_context/3` (single provider, scoped to `agent_id`) or
`Raxol.Agent.Memory.stack_context/3` (a stacked list).

## Memory LLM actions

Three LLM-callable actions reach the configured provider via `context[:memory]`
(the same wiring `Actions.Vfs` uses for `context[:vfs]`). They are added to
`available_actions/0` automatically when a memory provider is configured via
`use Raxol.Agent`.

| Action module               | Tool name         | Effect                                          |
| --------------------------- | ----------------- | ----------------------------------------------- |
| `Actions.Memory.Remember`   | `memory_remember` | Persist a fact (`content`, `type`, `tags`)      |
| `Actions.Memory.Recall`     | `memory_recall`   | Search cross-session memory (`query`, `limit`)  |
| `Actions.Memory.Forget`     | `memory_forget`   | Delete a memory by `id`                         |

`Raxol.Agent.Actions.Memory.actions/0` returns all three. Automatic post-turn
capture is not wired in `Memory.Manager`; writes are explicit via `memory_remember`
or the self-improve loop (see skills-procedural-memory.md).

## Session search

`Raxol.Agent.Memory.SessionSearch` is a GenServer BM25-lite inverted index over raw
conversation items: `start_link/1`, `index/2`, `attach/3`, `search/3`. Unlike memory
(curated facts), it returns the actual prior messages and tool results.

`Raxol.Agent.Actions.SessionSearch` (tool `session_search`) exposes it to the LLM,
reaching the index via `context[:session_search]` and returning
`{:error, :session_search_not_configured}` when absent. Input: `query` (required),
`limit` (default 10), `conversation_id` (restrict to one conversation).

## User model + auxiliary routing

`Raxol.Agent.UserModel` derives a per-user dialectic block on an auxiliary model and
injects it into the last user message (`build_user_context/1`, so a per-turn refresh
does not invalidate the cacheable system prefix). `Raxol.Agent.Auxiliary.resolve/2`
routes background tasks (curation, user-model refresh, session summary) to a cheaper
model per task kind; `resolve_chain/2` returns a fallback chain.

```elixir
{:ok, um} = Raxol.Agent.UserModel.start_link(name: MyUserModel)
Raxol.Agent.UserModel.refresh_async(um, "u-42", conversation_items, [])
ctx = Raxol.Agent.UserModel.get_context(um, "u-42")   # dialectic block or nil

cfg = Raxol.Agent.Auxiliary.resolve(:curation, [])     # -> ExecutorConfig for a cheap model
```

## Pitfalls

1. **Passing a bare string when history is expected** -- `Turn.run/3` accepts a
   prompt string or a list of message maps; mixing shapes drops prior turns.
2. **Confusing memory with session search** -- memory holds curated facts
   (`Memory.Record`); session search returns raw prior messages. Use the right one:
   `memory_recall` for a remembered decision, `session_search` for "what did we say".
3. **UserModel on the main model** -- route it through `Auxiliary` to a cheap model;
   refreshing the dialectic block on the primary model is wasteful.
