---
title: Agent Testing
impact: HIGH
impactDescription: Tests that skip Backend.Mock risk hitting real LLM APIs and producing flaky, expensive failures.
tags: raxol, agent, testing, mock, headless
---

# Agent Testing

Always use `Backend.Mock` -- never hit real LLM APIs in tests.

## TEA Agents via Headless

```elixir
test "agent processes request" do
  id = :"test_#{System.unique_integer([:positive])}"
  {:ok, ^id} = Raxol.Headless.start(MyAgent, id: id)
  on_exit(fn -> Raxol.Headless.stop(id) end)

  :ok = Raxol.Agent.Session.send_message(id, {:review, ["file.ex"]})
  Process.sleep(100)

  {:ok, model} = Raxol.Headless.get_model(id)
  assert model.status == :done

  # If agent has view/1:
  {:ok, screen} = Raxol.Headless.screenshot(id)
  assert screen =~ "complete"
end
```

Always clean up sessions -- use unique IDs + `on_exit` to avoid
`{:error, {:already_started, id}}` across tests.

## Process Agents

```elixir
test "process agent cycle" do
  {:ok, pid} = Raxol.Agent.Process.start_link(
    agent_id: :"test_#{System.unique_integer([:positive])}",
    agent_module: MyProcessAgent,
    backend: Raxol.Agent.Backend.Mock,
    backend_config: [response: "mock result"],
    tick_ms: 50
  )

  Process.push_event(pid, {:alert, "test"})
  Process.sleep(100)
  assert Process.get_status(pid).status in [:waiting, :thinking]
end
```

## Actions

Call directly -- no agent needed:

```elixir
assert {:ok, %{content: "hello"}} = ReadFile.call(%{path: "/tmp/test.txt"})
assert {:error, _} = ReadFile.call(%{})  # missing required :path
```

## Mock Backend Opts

```elixir
[response: "static"]                    # fixed response
[response_fn: fn -> "dynamic" end]      # function
[error: :rate_limited]                  # simulate error
[tool_calls: [%{"name" => "x", "arguments" => %{}}]]  # tool use
[latency_ms: 200]                       # simulate latency
```

## Turn driver + native backends

Drive a full turn with `Backend.Mock` -- never a real model or a native CLI:

```elixir
{:ok, out} =
  Raxol.Agent.Turn.run(MyAgent, "do the thing",
    backend: Raxol.Agent.Backend.Mock,
    backend_opts: [tool_calls: [%{"name" => "read_file", "arguments" => %{"path" => "/tmp/x"}}]],
    log: log, conversation_id: "t1")
```

For native backends (`Backend.ClaudeCode`/`Cursor`), test the harness in isolation:
feed captured NDJSON lines to `Raxol.Agent.Harness.StreamJson.parse_line/1` and assert
the parsed events -- do not spawn the real `claude`/`cursor` CLI in tests.

## Teams

```elixir
test "team starts all agents" do
  {:ok, sup} = Raxol.Agent.Team.start_link(
    team_id: :"team_#{System.unique_integer([:positive])}",
    coordinator: {TestCoord, [id: :coord]},
    workers: [{TestWorker, [id: :w1]}]
  )

  assert {:ok, _} = Session.get_model(:coord)
  assert {:ok, _} = Session.get_model(:w1)
  Supervisor.stop(sup)
end
```
