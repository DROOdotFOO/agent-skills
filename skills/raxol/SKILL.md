---
name: raxol
description: >
  Raxol terminal framework for TUI apps and AI agents in Elixir (v2.6, 17-package monorepo).
  TRIGGER when: code imports Raxol modules (Raxol.Agent, Raxol.Core, Raxol.MCP,
  Raxol.LiveView, Raxol.Workflow, Raxol.Headless, Raxol.Agent.Harness, Raxol.Agent.Skills,
  Raxol.Agent.Journal, Raxol.Gateway, Raxol.Telegram, Raxol.Watch, Raxol.Speech,
  Raxol.Agent.ClientProtocol, Raxol.AgentClientProtocol), mix.exs lists :raxol / :raxol_agent /
  :raxol_core / :raxol_mcp / :raxol_terminal / :raxol_gateway / :raxol_telegram / :raxol_watch /
  :raxol_speech / :raxol_agent_client_protocol as a dependency, commands "mix raxol.code" or
  "mix raxol.p", user asks about building TUI apps or AI agents with Raxol, agent
  memory/self-improvement, agent skills / procedural memory, the coding agent harness, the
  workflow engine, blast radius / spend gate, or Raxol headless/MCP tools.
  DO NOT TRIGGER when: general Elixir patterns (use droo-stack skill),
  Claude API / Anthropic SDK usage (use claude-api skill), agentic commerce / payments /
  the Agent COMMERCE Protocol (raxol_acp) / agent wallets / ACP job sessions
  (use raxol-payments skill -- note this is distinct from raxol_agent_client_protocol, the
  Agent CLIENT Protocol, which IS in scope), the Symphony coding-agent orchestrator
  (use raxol-symphony skill), or other TUI frameworks (Scenic, Termbox, etc.).
metadata:
  author: droo
  version: "2.6.0"
  tags: elixir, raxol, tui, agents, mcp, headless, workflow, orchestration, harness, skills, gateway, speech, telegram, watch, acp-client, surfaces
---

# Raxol Skill

Elixir TEA framework for terminal UIs + AI agent orchestration. The same TEA model
runs in the terminal, browser (LiveView), SSH, and as MCP tools/resources. OTP
provides supervision, crash isolation, and hot reload.

Raxol v2.6 is a 17-package monorepo (targets Elixir 1.20 / OTP 29, supports 1.17+).
The terminal emulator + termbox2 NIF were extracted from the root `raxol` package into
`raxol_terminal`; `raxol` is now the umbrella / full-framework package. The 15 packages
this skill covers:

- `raxol_core` -- TEA runtime, buffer/rendering, events, directives, telemetry
- `raxol` -- umbrella / full-framework package (pulls in the modular packages)
- `raxol_terminal` -- VT/ANSI emulator, screen buffers, driver, input, sessions,
  termbox2 NIF (extracted from `raxol` in v2.6)
- `raxol_agent` -- agent framework: TEA/Process agents, turn driver, memory,
  self-improving skills, journal, backends, coding harness, teams
- `raxol_mcp` -- MCP server/client: tool auto-derivation, focus lens, resources
- `raxol_liveview` -- Phoenix LiveView bridge (buffer -> HTML, a11y)
- `raxol_plugin` -- plugin SDK (`mix raxol.gen.plugin`)
- `raxol_sensor` -- sensor fusion for Process agents
- `raxol_gateway` -- unified messaging gateway: one daemon, many chat platforms via a
  shared adapter contract, process-per-chat sessions, DM pairing auth
- `raxol_speech` -- speech surface: TTS reads a11y announcements, STT captures voice
  input via Bumblebee/Whisper and injects events
- `raxol_telegram` -- Telegram surface: renders TEA apps as monospace code blocks with
  inline-keyboard navigation
- `raxol_watch` -- Watch notification bridge: glanceable summaries to Apple Watch (APNS)
  and Wear OS (FCM); tap actions route back as events
- `raxol_agent_client_protocol` -- Elixir/OTP implementation of ACP (Agent CLIENT
  Protocol): JSON-RPC 2.0 between editors and coding agents, pluggable transports
- `raxol_cli` -- the `raxol` command: interactive AI agent + toolkit as a self-contained
  binary via npm wrapper
- `raxol_console` -- console runtime: boots an ACP Console agent package onto the gateway stack

Payments / the Agent COMMERCE Protocol (`raxol_payments`, `raxol_acp`) and the Symphony
orchestrator (`raxol_symphony`) have their own skills -- see below. Do not confuse
`raxol_acp` (Agent Commerce Protocol, payments) with `raxol_agent_client_protocol`
(Agent Client Protocol, in scope here).

## What You Get

- TEA agent and Process agent patterns with lifecycle examples
- Turn driver + memory stack + self-improving skills (v2.6)
- Workflow engine: graph DSL, checkpointing, human-in-the-loop, saga rollback
- AI backends (HTTP, Mock, native ClaudeCode/Cursor, OpenRouter) + harness selection
- MCP server (auto-derive tools from the widget tree) and MCP client
- LiveView surface (buffer -> HTML, themes, accessibility)
- Multi-agent orchestration (teams, cockpit, message protocol)
- Agent skills / procedural memory + the journal (blast radius, spend gate)
- Coding agent harness (`mix raxol.code`, `mix raxol.p`) with tool classification
- Chat surfaces via the gateway (Telegram, Discord, email) + speech (TTS/STT)
- Agent Client Protocol: editor <-> agent JSON-RPC (distinct from ACP payments)
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
| Agent skills / procedural memory  | `agents/skills-procedural-memory.md` |
| Coding agent harness (raxol.code) | `agents/coding-harness.md`     |
| Reusable actions / LLM tools      | `agents/actions-pipelines.md`  |
| Multi-agent teams / cockpit       | `agents/teams-orchestrator.md` |
| Orchestrate steps as a graph      | `workflow/graph.md`            |
| AI backend + harness selection    | `ai/backends.md`               |
| Consume external MCP servers      | `ai/mcp-client.md`             |
| Editor<->agent ACP (Zed, not payments) | `ai/agent-client-protocol.md` |
| Expose your app as MCP tools      | `mcp/server.md`                |
| Render a TEA app in LiveView      | `surfaces/liveview.md`         |
| Chat surfaces: gateway / Telegram | `surfaces/messaging.md`        |
| Speech surface (TTS/STT)          | `surfaces/speech.md`           |
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
