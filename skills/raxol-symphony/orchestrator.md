---
title: Orchestrator, Trackers + Runners
impact: HIGH
impactDescription: A misconfigured tracker or runner kind fails schema validation and the orchestrator never starts runs.
tags: raxol, symphony, orchestrator, tracker, runner
---

# Orchestrator, Trackers + Runners

## Orchestrator (`Raxol.Symphony.Orchestrator`)

Polls the tracker for candidate issues, ensures an isolated workspace per issue, and runs
a runner until the issue reaches a terminal state (or pauses).

```elixir
{:ok, pid} = Raxol.Symphony.Orchestrator.start_link(
  config: config, runner_module: Raxol.Symphony.Runners.RaxolAgent)

snap   = Raxol.Symphony.Orchestrator.snapshot(pid)   # active/paused/pending runs
:ok    = Raxol.Symphony.Orchestrator.refresh(pid)    # poll now
paused = Raxol.Symphony.Orchestrator.paused(pid)     # %{issue_id => pause info}
:ok    = Raxol.Symphony.Orchestrator.resume_run(pid, issue_id, resume_value)
:ok    = Raxol.Symphony.Orchestrator.stop_run(pid, issue_id)
```

Usually you start the whole supervision tree with `Raxol.Symphony.start_link(workflow_path:)`
rather than the orchestrator directly.

## Workspace isolation

`Raxol.Symphony.Workspace.ensure/2` creates/returns the per-issue workspace;
`Raxol.Symphony.PathSafety` guards it:

```elixir
{:ok, %{path: path, key: key, created_now: _}} = Workspace.ensure(config, "MT-123")
key = Raxol.Symphony.PathSafety.sanitize_key("MT/123")   # -> "MT_123"
{:ok, p} = Raxol.Symphony.PathSafety.workspace_path(root, "MT-123")
Raxol.Symphony.PathSafety.assert_cwd!(path)              # or raises
```

`Workspace` also runs before/after-run hooks (`run_before_run_hook/2`, etc.).

## Trackers (`Raxol.Symphony.Tracker`)

Behaviour: `fetch_candidate_issues/1`, `fetch_issues_by_states/2`,
`fetch_issue_states_by_ids/2`. An `Issue` has `id`, `identifier`, `title`, `state`;
`Issue.terminal?/2` / `active?/2` test membership against the configured state lists.

| Tracker  | Module                              | Config                                              |
| -------- | ----------------------------------- | --------------------------------------------------- |
| Linear   | `Raxol.Symphony.Trackers.Linear`    | `project_slug`, `api_key`; Relay cursor pagination  |
| GitHub   | `Raxol.Symphony.Trackers.GitHub`    | `owner/repo`; `state/<slug>` labels                 |
| Memory   | `Raxol.Symphony.Trackers.Memory`    | in-process; tests (`put_issue/2`, `transition/3`)   |

## Runners (`Raxol.Symphony.Runner`)

Callback `run(issue, config, opts)` returns:

- `:ok` -- run succeeded; schedules a continuation
- `{:error, reason}` -- failure; exponential-backoff retry
- `{:pause, reason, token}` -- park in the paused map until resumed

`opts`: `:parent` (pid), `:attempt`, `:workspace_path`, and on resume `:resume_token` /
`:resume_value`. Optional `pause_reasons/0` declares the reasons a runner may emit.

| Runner              | Module                                        | Notes                                   |
| ------------------- | --------------------------------------------- | --------------------------------------- |
| RaxolAgent          | `Raxol.Symphony.Runners.RaxolAgent`           | primary; raxol_agent + self-improve     |
| Codex               | `Raxol.Symphony.Runners.Codex`                | JSON-RPC over stdio; `:awaiting_approval`|
| AgentSession        | `Raxol.Symphony.Runners.RaxolAgentSession`    | drives a `use Raxol.Agent` module       |
| Review              | `Raxol.Symphony.Runners.Review`               | implement -> pause -> review on resume  |
| Noop                | `Raxol.Symphony.Runners.Noop`                 | test-only (Director-scripted)           |

The RaxolAgent runner is configured under `runner.agent` in WORKFLOW.md (backend, model,
`max_turns`, optional `pause_detector`, `sandboxes`, `policies`).

## Config validation

`Raxol.Symphony.Config.Schema.validate/2` rejects unknown tracker/runner kinds early.
Trackers: `linear` / `github` / `memory`. Runners: `raxol_agent` / `codex` / `review`.

## Pitfalls

1. **Runner outside its workspace** -- always run in `opts[:workspace_path]`; PathSafety
   is there to stop escapes.
2. **Unknown kind** -- schema validation fails fast; check the `kind` strings.
3. **Ignoring `{:pause, ...}`** -- a runner that blocks instead of pausing can't be
   resumed by a surface or the `Resumer`.
