---
name: raxol
description: >
  Raxol terminal framework for TUI apps and AI agents in Elixir (v2.6, 15-package monorepo).
  TRIGGER when: code imports Raxol modules (Raxol.Agent, Raxol.Core, Raxol.MCP,
  Raxol.LiveView, Raxol.Workflow, Raxol.Headless), mix.exs lists :raxol / :raxol_agent /
  :raxol_core / :raxol_mcp as a dependency, user asks about building TUI apps or AI agents
  with Raxol, agent memory/self-improvement, the workflow engine, or Raxol headless/MCP tools.
  DO NOT TRIGGER when: general Elixir patterns (use droo-stack skill),
  Claude API / Anthropic SDK usage (use claude-api skill), agentic commerce / payments /
  ACP job sessions (use raxol-payments skill), the Symphony coding-agent orchestrator
  (use raxol-symphony skill), or other TUI frameworks (Scenic, Termbox, etc.).
metadata:
  author: droo
  version: "2.6.0"
  tags: elixir, raxol, tui, agents, mcp, headless, workflow, orchestration
---

# Raxol Skill

Elixir TEA framework for terminal UIs + AI agent orchestration. The same TEA model
runs in the terminal, browser (LiveView), SSH, and as MCP tools/resources. OTP
provides supervision, crash isolation, and hot reload.

Raxol v2.6 is a 15-package monorepo (Elixir 1.20 / OTP 29). The packages this skill
covers:

- `raxol_core` -- TEA runtime, buffer/rendering, events, directives, telemetry
- `raxol` -- umbrella + terminal surface (termbox2 NIF + IO fallback)
- `raxol_agent` -- agent framework: TEA/Process agents, turn driver, memory,
  self-improving skills, backends, harnesses, teams
- `raxol_mcp` -- MCP server/client: tool auto-derivation, focus lens, resources
- `raxol_liveview` -- Phoenix LiveView bridge (buffer -> HTML, a11y)
- `raxol_plugin`, `raxol_sensor` -- plugin SDK, sensor fusion

Payments/ACP (`raxol_payments`, `raxol_acp`) and the Symphony orchestrator
(`raxol_symphony`) have their own skills -- see below.

## What You Get

- TEA agent and Process agent patterns with lifecycle examples
- Turn driver + memory stack + self-improving skills (v2.6)
- Workflow engine: graph DSL, checkpointing, human-in-the-loop, saga rollback
- AI backends (HTTP, Mock, native ClaudeCode/Cursor, OpenRouter) + harness selection
- MCP server (auto-derive tools from the widget tree) and MCP client
- LiveView surface (buffer -> HTML, themes, accessibility)
- Multi-agent orchestration (teams, cockpit, message protocol)
- Headless sessions and agent testing patterns (unit, integration, E2E)

## Two Agent Models

|                | TEA Agent (`use Raxol.Agent`)       | Process Agent (`use Raxol.Agent.UseProcess`) |
| -------------- | ----------------------------------- | -------------------------------------------- |
| Loop           | Message-driven (`update/2`)         | Tick-driven (observe/think/act)              |
| Rendering      | Optional `view/1`                   | Headless only                                |
| Input          | Messages from agents, commands, MCP | Events buffer, directives                    |
| Best for       | Agents with UI, reactive workflows  | Autonomous background agents                 |
| Crash recovery | OTP restart, fresh `init/1`         | `context_snapshot` + `restore_context`       |
| AI backend     | Manual (call in async commands)     | Built-in via Strategy                        |

For a full LLM chat turn (memory + skills + user model + tool loop) use the
`Raxol.Agent.Turn` driver -- see `agents/turn-memory.md`.

## See also

- `raxol-payments` -- agentic commerce: Xochi/Riddler/ACP, agent wallets, privacy tiers
- `raxol-symphony` -- tracker-driven coding-agent orchestrator (Symphony)
- `droo-stack` -- general Elixir patterns (pipes, pattern matching, ExUnit)
- `design-ux` -- TUI design principles (terminal layout, box-drawing, density)
- `claude-api` -- Anthropic SDK integration in Elixir

## Reading Guide

| Task                              | File                           |
| --------------------------------- | ------------------------------ |
| Build a TEA agent + messaging     | `agents/tea-agent.md`          |
| Build an autonomous agent         | `agents/process-agent.md`      |
| Full LLM turn: memory + skills    | `agents/turn-memory.md`        |
| Reusable actions / LLM tools      | `agents/actions-pipelines.md`  |
| Multi-agent teams / cockpit       | `agents/teams-orchestrator.md` |
| Orchestrate steps as a graph      | `workflow/graph.md`            |
| AI backend + harness selection    | `ai/backends.md`               |
| Consume external MCP servers      | `ai/mcp-client.md`             |
| Expose your app as MCP tools      | `mcp/server.md`                |
| Render a TEA app in LiveView      | `surfaces/liveview.md`         |
| Headless sessions + MCP tools     | `headless/sessions.md`         |
| Testing agents and actions        | `testing/agent-testing.md`     |

## Message Protocol

All TEA agents receive these in `update/2`. Defined once here, referenced
from other files.

```elixir
# Async message from another agent
{:agent_message, from_id, payload}

# Sync call -- MUST reply with send(pid, {:agent_reply, ref, reply})
{:call, caller_pid, ref, message}

# Team broadcast
{:team_broadcast, team_id, payload}

# Async command / directive results
{:command_result, result}
{:command_result, {:shell_result, %{output: string, exit_status: int}}}
{:command_result, {:action_result, module, result_map}}
{:command_result, {:action_error, module, reason}}
{:command_result, {:pipeline_result, result_map}}
{:command_result, {:pipeline_error, step_module, reason}}
```

## Key Conventions

- All agents auto-register in `Raxol.Agent.Registry` by `:id`
- Always return `{model, command}` from `update/2`, never bare `model`
- `view/1` returning `nil` = headless (no rendering overhead)
- Effects are struct-based `Directive`s (v2.6): `Raxol.Core.Runtime.Directive`
  (`stop/1`, `schedule/2`, `spawn_task/1`) and `Raxol.Agent.Directive`
  (`async/1`, `shell/2`, `send_agent/2`). The `use Raxol.Agent` helpers wrap these.
- Session agents register as `agent_id`, Process agents as `{:process, agent_id}`,
  MCP clients as `{:mcp_client, name}`
- Agent package: `packages/raxol_agent/`

## Common Pitfalls

1. **Wrong update/2 return** -- must return `{model, Command.none()}` not bare `model`
2. **Forgetting call reply** -- `{:call, pid, ref, msg}` requires `send(pid, {:agent_reply, ref, reply})`; caller blocks with timeout
3. **Mixing agent models** -- TEA callbacks and ProcessBehaviour callbacks are separate behaviours
4. **Sync call deadlocks** -- Agent A calls B, B calls A = deadlock. Break cycles with async `send_agent/2`
5. **String vs atom keys** -- Headless `send_key` uses atoms for special keys (`:tab`), strings for characters (`"q"`)
6. **Real backends in tests** -- always use `Backend.Mock`, never HTTP

## Design Context

Raxol treats each rendering surface (terminal, web, SSH, MCP) as a functor
from the TEA model. Same `update/2`, same model, different projections. In v2.6
MCP is a first-class surface (`raxol_mcp`): widgets auto-export tools via the
`Raxol.MCP.ToolProvider` behaviour, model state is exposed via `ResourceProvider`,
and `FocusLens` filters tools by attention. When building features, consider how
they surface as MCP tools -- see `mcp/server.md`.
