---
title: WORKFLOW.md, Graph Adapter + Evidence
impact: MEDIUM
impactDescription: A failed WORKFLOW.md reload silently serves stale config; missing evidence hooks leave runs unauditable.
tags: raxol, symphony, workflow, evidence, hot-reload
---

# WORKFLOW.md, Graph Adapter + Evidence

## WORKFLOW.md

A workflow is YAML front-matter (`config`) plus a Liquid prompt template. `Workflow.load/1`
/ `Workflow.parse/1` produce `%{config, prompt_template}`; `Config.from_workflow/2` builds
the `Config` struct.

```markdown
---
tracker: {kind: github, project_slug: "owner/repo", api_key: $GITHUB_TOKEN}
runner:  {kind: raxol_agent, agent: {backend: anthropic, model: claude-sonnet-4-6}}
---
Implement issue {{ issue.identifier }}. Attempt {{ attempt }}.
```

`Raxol.Symphony.PromptBuilder.build(issue, template, attempt)` renders the prompt.

## Hot-reload (`WorkflowStore`)

Watches the file and reloads on change (debounced). On a bad edit it keeps the
last-known-good config and records the error.

```elixir
{:ok, ws} = Raxol.Symphony.WorkflowStore.start_link(path: "WORKFLOW.md", watch?: true)
cfg = Raxol.Symphony.WorkflowStore.get(ws)
:ok = Raxol.Symphony.WorkflowStore.subscribe(ws)   # {:workflow_store, :reloaded, Config.t}
err = Raxol.Symphony.WorkflowStore.last_error(ws)   # nil when healthy
```

## Graph adapter (saga pipeline)

`Raxol.Symphony.Workflow.GraphAdapter.from_workflow/2` compiles the run into a
`Raxol.Workflow.Compiled` graph (see the `raxol` skill's `workflow/graph.md`). Canonical
pipeline:

```
__start__ -> tracker_poll -> candidate_selection
  -> runner_dispatch -> [runner_wait -> runner_dispatch]*
  -> evidence_collection -> completion -> __end__
```

This is what gives Symphony saga-style retries and durable, resumable runs.

## Evidence framework

`Raxol.Symphony.Evidence` is a struct (`workspace`, `repo`, `ref`, `issue_number`, `ci`,
`pr_comments`, `complexity`, `recordings`, `errors`) populated by pluggable backends, each
implementing `collect(evidence, config, opts)`:

| Backend                              | Populates                                             |
| ------------------------------------ | ----------------------------------------------------- |
| `Evidence.GitHub`                    | latest CI run for `ref`, recent PR/issue comments     |
| `Evidence.Complexity`                | `cloc --json` (falls back to an Elixir SLOC counter)  |
| `Evidence.Recording`                 | scans `.raxol_symphony/*.cast` asciinema files        |
| `Evidence.Capture` (GenServer)       | records an asciicast v2 during the run                |

```elixir
subject = Raxol.Symphony.Evidence.Subject.from_workspace(path, issue_number: 42)
subject = Raxol.Symphony.Evidence.Subject.augment(subject, config, issue)

{:ok, cap} = Raxol.Symphony.Evidence.Capture.start_link(path: cast_path, title: "MT-42")
Raxol.Symphony.Evidence.Capture.record(cap, event)
Raxol.Symphony.Evidence.Capture.stop(cap)
```

Evidence collection is fail-soft: a missing `cloc` or unreachable GitHub degrades
gracefully rather than failing the run.

## Pitfalls

1. **Silent stale config** -- after editing WORKFLOW.md, check `last_error/1`; a parse
   error keeps the old config.
2. **Expecting hard failures from evidence** -- backends fail soft; assert on the
   populated struct, not on exceptions.
3. **Liquid vs plain text** -- the prompt is a Liquid template; unescaped `{{ }}` that
   isn't a known var renders empty.
