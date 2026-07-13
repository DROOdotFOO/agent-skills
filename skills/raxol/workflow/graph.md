---
title: Workflow Engine
impact: HIGH
impactDescription: Missing structural validation or a saver silently drops resumable state and human-in-the-loop pauses.
tags: raxol, workflow, graph, checkpoint, saga
---

# Workflow Engine (`Raxol.Workflow`)

LangGraph-style state-machine graphs for multi-step agent work. Build a `Graph`,
`compile/2` it (6-step structural validation), then `invoke`/`async_invoke`/
`stream_events`. State is a single map threaded through nodes.

Package: `packages/raxol_core` (`Raxol.Workflow.*`).

## Build + compile + run

```elixir
alias Raxol.Workflow.Graph

{:ok, compiled} =
  Graph.new(:summarizer)
  |> Graph.add_node(:fetch,  fn s -> {:ok, Map.put(s, :data, fetch())} end)
  |> Graph.add_node(:render, fn s -> {:ok, Map.put(s, :out, render(s.data))} end)
  |> Graph.add_edge(:__start__, :fetch)
  |> Graph.add_edge(:fetch, :render)
  |> Graph.add_edge(:render, :__end__)
  |> Graph.compile()

result = Raxol.Workflow.Compiled.invoke(compiled, %{})
```

Nodes return `{:ok, state}` (or `{:error, reason}`). `:__start__` and `:__end__`
are the reserved terminal node ids.

## Graph builder

```elixir
Graph.new(atom | binary)
Graph.add_node(g, id, fun_or_term)
Graph.add_edge(g, from_id, to_id)
Graph.add_guarded_edge(g, from, to, fn state -> boolean end)
Graph.add_conditional_edge(g, from, [candidates], fn state -> chosen_id end)
Graph.add_join(g, id, [wait_for_ids], opts)      # barrier over parallel branches
Graph.add_channel(g, name, opts)                 # typed reducer for concurrent writes
Graph.compile(g, opts)                            # {:ok, Compiled.t} | {:error, err}
```

Use `add_channel/3` + `add_join/4` for parallel branches: each branch writes to a
typed channel, the join reduces them before the downstream node runs.

## Execution API (`Raxol.Workflow.Compiled`)

```elixir
Compiled.invoke(compiled, input, opts)         # synchronous -> result
Compiled.async_invoke(compiled, input, opts)   # {:ok, %{run_id, pid, ref}}
Compiled.stream_events(compiled, input, opts)  # Enumerable of node events
Compiled.resume(compiled, run_id, value, opts) # resume a paused run
Compiled.resume_events(compiled, run_id, value, opts)
```

## Human-in-the-loop (interrupt / resume)

Pause a run from inside a node with `Raxol.Workflow.interrupt/1`; it throws until a
matching `resume/4` supplies the value. Requires a checkpoint saver.

```elixir
Graph.add_node(:approve, fn state ->
  decision = Raxol.Workflow.interrupt(%{ask: "approve?", diff: state.diff})
  {:ok, Map.put(state, :approved, decision)}
end)

{:ok, compiled} = Graph.compile(g, saver: Raxol.Workflow.Checkpoint.Saver.Ets)

# later, after a human decides:
result = Compiled.resume(compiled, run_id, true, [])
```

`resume/4` returns `{:error, :no_saver_configured}` or `{:error, :no_checkpoint}`
when there is nothing to resume.

## Failure policy (compile opts)

```elixir
Graph.compile(g,
  failure_policy: :retry,    # :halt (default) | :retry | :compensate (saga)
  max_attempts: 3,
  retry_backoff_ms: 100,
  step_timeout_ms: 60_000,
  run_timeout_ms: 3_600_000,
  saver: Raxol.Workflow.Checkpoint.Saver.Ets  # Ets (default) | Dets | Postgrex
)
```

`:compensate` runs saga-style rollback of completed nodes on failure.

## Pitfalls

1. **No saver, but `interrupt/1` used** -- pause has nowhere to persist; `resume`
   returns `{:error, :no_saver_configured}`. Always pass a `:saver` for HITL.
2. **Forgetting `:__start__` / `:__end__` edges** -- `compile/2` fails validation.
3. **Mutating shared state across parallel branches** -- use `add_channel/3`
   reducers + `add_join/4`, not direct map writes, or concurrent updates race.
