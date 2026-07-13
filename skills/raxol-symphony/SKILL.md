---
name: raxol-symphony
description: >
  Symphony: the Raxol tracker-driven coding-agent orchestrator (raxol_symphony, pre-alpha).
  Turns tracker issues into autonomous agent runs in isolated workspaces, surfaces evidence
  (CI/PR/asciinema), and supports human-in-the-loop paused runs across six surfaces.
  TRIGGER when: mix.exs lists :raxol_symphony; code imports Raxol.Symphony.*; there is a
  WORKFLOW.md driving an orchestrator; user asks about tracker-driven agent orchestration,
  Symphony runners (RaxolAgent/Codex), evidence capture, or paused-run resume with Raxol.
  DO NOT TRIGGER when: building a single Raxol agent or the core framework (use raxol skill);
  agent payments / ACP job sessions (use raxol-payments skill); generic multi-agent system
  design without Symphony (use agent-designer skill); the Claude Agent SDK (use claude-api).
metadata:
  author: droo
  version: "0.1.0"
  tags: elixir, raxol, symphony, orchestrator, coding-agent, tracker
---

# Raxol Symphony Skill

`raxol_symphony` (v0.1, pre-alpha) is an OTP port of OpenAI's Symphony: an orchestrator
that turns tracker work into autonomous coding-agent runs. Each issue gets an isolated
workspace, runs an agent until a workflow-defined handoff state, and surfaces evidence
(CI, PR comments, asciinema walkthrough) so engineers manage outcomes, not prompts.

Config is a `WORKFLOW.md` (YAML front-matter + a Liquid prompt template), hot-reloaded on
change. Pre-alpha: APIs may shift.

## What You Get

- Orchestrator loop: poll tracker -> isolate workspace -> run runner -> collect evidence
- Runners: RaxolAgent (primary), Codex (JSON-RPC parity), AgentSession, Review, Noop
- Trackers: Linear (GraphQL), GitHub (state labels), Memory (tests)
- WORKFLOW.md hot-reload + a workflow graph adapter (saga-style)
- Evidence framework: CI, PR comments, complexity (cloc), asciinema recordings
- Six surfaces + a first-class paused-run substrate (pause/resume across surfaces)

## Quickstart

```elixir
{:ok, _pid} = Raxol.Symphony.start_link(workflow_path: "WORKFLOW.md")
```

```markdown
<!-- WORKFLOW.md -->
---
tracker:
  kind: linear
  project_slug: demo
  api_key: $LINEAR_API_KEY
  active_states: ["Todo", "In Progress"]
  terminal_states: ["Done", "Cancelled"]
runner:
  kind: raxol_agent
  agent:
    backend: anthropic
    model: claude-sonnet-4-6
    max_turns: 20
---
You are working on issue {{ issue.identifier }}: {{ issue.title }}.
```

## See also

- `raxol` -- core agent/TUI framework Symphony runs agents on
- `raxol-payments` -- ACP job sessions used by the paused-run resume flow
- `agent-designer` -- general multi-agent orchestration patterns (non-Symphony)
- `prd-to-plan` / `qa` -- feeding a tracker with well-formed issues

## Reading Guide

| Task                                      | File                       |
| ----------------------------------------- | -------------------------- |
| Orchestrator, trackers, runners, config   | `orchestrator.md`          |
| WORKFLOW.md, graph adapter, evidence      | `workflows-evidence.md`    |
| Surfaces + pause/resume + sandboxes       | `surfaces-pause.md`        |

## Key Conventions

- One workspace per issue; `PathSafety` sanitizes identifiers and asserts paths stay
  inside the workspace root. Never run an agent outside its workspace.
- A runner returns `:ok` (retry-continue), `{:error, reason}` (backoff retry), or
  `{:pause, reason, token}` (park in the orchestrator's paused map).
- The Review runner's `Contract` deliberately carries no workspace reference -- reviewer
  isolation is an invariant.

## Common Pitfalls

1. **Blocking on human input inline** -- return `{:pause, reason, token}` and let a
   surface/`Resumer` resume; don't sleep the runner.
2. **Bad WORKFLOW.md** -- `WorkflowStore` falls back to the last-known-good config and
   records `last_error/1`; check it after edits.
3. **Assuming production-ready** -- v0.1 pre-alpha; pin versions and expect churn.
