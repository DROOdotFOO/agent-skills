---
title: Skills (Procedural Memory)
impact: HIGH
impactDescription: Agents read and self-author reusable SKILL.md procedures; misconfiguring the store or created_by tag silently disables curation or corrupts the user's skill library.
tags: raxol, agent, skills, procedural-memory, self-improve, curator
---

# Skills (Procedural Memory)

Reusable, named procedures an agent reads on demand and, via the curation loop,
authors itself. Each skill is an agentskills.io `SKILL.md` on disk. This is the
procedural counterpart to semantic memory (see [turn-memory.md](turn-memory.md)):
memory holds facts, skills hold multi-step how-tos.

Four moving parts:

- `Raxol.Agent.Skill` -- pure parse/render of one `SKILL.md`.
- `Raxol.Agent.Skills.Store` -- disk-backed warm index + usage telemetry.
- `Raxol.Agent.Actions.Skills.{List,View,Manage}` -- the LLM-callable tools.
- `Raxol.Agent.Curator` / `Raxol.Agent.SelfImprove` -- the write-back loop.

## Enabling it

The store is a supervised singleton, gated on config. `Raxol.Agent.Supervisor`
starts `Raxol.Agent.Skills.Store` only when `:skills_provider` is exactly that
module:

```elixir
# config/config.exs
config :raxol_agent,
  skills_provider: Raxol.Agent.Skills.Store,
  skills_root: "~/.raxol/skills",              # managed (writable). default: ~/.raxol/skills
  skills_external_dirs: ["~/.agents/skills"],  # read-only. default: ~/.agents/skills
  skills_store_path: "~/.raxol/skills.dets"    # optional: persist usage telemetry

# Optional: the background ager (see below). Requires a :skills tuple.
config :raxol_agent,
  curator: [skills: {Raxol.Agent.Skills.Store, []}]
```

Per-agent, override `skills_provider/0` (from `use Raxol.Agent`) to turn on the
skill actions for that agent:

```elixir
defmodule ResearchAgent do
  use Raxol.Agent
  def skills_provider, do: Raxol.Agent.Skills.Store
  # available_actions/0 now auto-includes the three skill actions.
end
```

When `skills_provider/0` is set, `available_actions/0` appends
`Raxol.Agent.Actions.Skills.actions()` automatically -- you do not list them by
hand. The agent must still put the provider tuple under `context[:skills]` when
invoking a Strategy or `Raxol.Agent.Stream` (see Wiring below).

## SKILL.md format

Frontmatter (YAML) plus a markdown body. `name` is required; `description`,
`version`, `category`, `created_by` are modeled; every other key is preserved
under `:metadata` across a round trip.

```markdown
---
name: rebase-onto-main
description: Rebase a feature branch onto main and resolve conflicts
category: git
version: "1"
created_by: agent
---
# Rebase onto main

1. `git fetch origin main`
2. `git rebase origin/main`
3. On conflict: resolve, `git add -p`, `git rebase --continue`
```

`created_by` decodes to `:agent`, `:user`, or `nil` (unknown values become
`nil` -- never `String.to_atom/1` on file content). This tag decides what the
Curator may touch. `parse(render(skill))` round-trips for scalars, scalar
lists, and one-level metadata maps.

## Managed vs external sources

The Store scans `**/SKILL.md` under two kinds of root and tags each entry:

- `:managed` -- under `skills_root`, **writable**. All `skill_manage` writes,
  `create/2`, `patch/2`, `delete/2`, `archive/2` touch only these.
- `:external` -- under `external_dirs`, **read-only**. Lets the agent read the
  user's existing library (e.g. `~/.agents/skills`) but never mutate it.

A managed skill wins over an external skill of the same name. Attempting to
`patch`/`delete`/`archive` an `:external` skill returns `{:error, :read_only_skill}`.

Disk is the source of truth: skills are re-read every boot, so no stale content
outlives its file. Only usage telemetry (`use_count`, `view_count`,
`last_used_at`, `state`, `pinned`) is the store's own state, persisted to DETS
when `skills_store_path` is set.

## The three actions

All reach the store via `context[:skills]` and return `{:error, :skills_not_configured}`
if it is absent. This mirrors how `Actions.Memory` reaches `context[:memory]`.

| Tool           | Level                          | Store call                          |
| -------------- | ------------------------------ | ----------------------------------- |
| `skills_list`  | metadata only (cheap)          | `list/1`                            |
| `skill_view`   | one skill's body / support file| `view/3` (bumps `view_count`)       |
| `skill_manage` | create / patch / edit / delete | `create/2` `patch/3` `delete/2`     |

Progressive disclosure: the LLM calls `skills_list` to see names +
descriptions, then `skill_view` to read the one it needs -- the full body is
never dumped into context up front. `skill_view` with a relative `path` reads a
supporting file inside the skill dir; absolute paths or any `..` segment are
rejected (`{:error, :unsafe_path}`).

Foreground `skill_manage create` tags the skill `created_by: :user` -- it is
user-directed, so the Curator will never age or rewrite it.

## Wiring via context[:skills]

Build the tuple with `Raxol.Agent.Skills.provider_context/2` and pass the same
`opts` on every store call. Store functions take **keyword opts** (notably
`:server` for a non-default registered name) -- never a positional pid.

```elixir
# Build once from the configured provider, or nil when skills are disabled.
provider = Raxol.Agent.Skills.default_provider()          # reads :skills_provider
skills = Raxol.Agent.Skills.provider_context(provider)    # {Store, []} | nil

context = %{skills: skills, memory: memory_tuple}          # feed to Strategy / Stream

# Direct store use (opts is a keyword list; no store pid argument):
[%{name: _, category: _, description: _, state: _, source: _} | _] =
  Raxol.Agent.Skills.Store.list([])

{:ok, %Raxol.Agent.Skill{body: body}} =
  Raxol.Agent.Skills.Store.get("rebase-onto-main", [])

{:ok, ^body} = Raxol.Agent.Skills.Store.view("rebase-onto-main", nil, [])
:ok = Raxol.Agent.Skills.Store.record_use("rebase-onto-main", [])
```

INCORRECT -- passing a store pid positionally:

```elixir
Raxol.Agent.Skills.Store.get(pid, "rebase-onto-main")  # no such arity
```

CORRECT -- target a named store via opts:

```elixir
Raxol.Agent.Skills.Store.get("rebase-onto-main", server: :my_store)
```

## Curation / self-improve loop

Two background writers, both operating only on `created_by: :agent` skills.

`Raxol.Agent.SelfImprove` runs after a `react/2` turn is recorded. If the turn
qualifies (no error item AND at least `min_tool_calls` tool calls, default 5),
an unlinked `Task` reviews the transcript on an auxiliary (cheap) model and
writes durable knowledge: facts -> `Raxol.Agent.Memory`, reusable procedures ->
`Skills.Store.create/2` with `created_by: :agent`. It only appends; it never
calls `update/2`, never mutates the live conversation, and a crash is logged,
not propagated. Enable via the `self_improve/0` map:

```elixir
def self_improve,
  do: %{enabled: true, model: "claude-haiku-4-5", min_tool_calls: 5}
```

`Raxol.Agent.Curator` ages what SelfImprove writes. Its deterministic pass moves
a skill `active -> stale -> archived` as it goes unused
(`stale_after_days: 30`, `archive_after_days: 90`); archived skills move under
`<root>/.archive/` and drop out of `skills_list`. It touches only
`created_by: :agent`, `source: :managed`, unpinned skills -- user, external, and
pinned skills are left alone. Passes are gated on time + idleness
(`interval_hours: 168`, `min_idle_hours: 2`) and write a `.tar.gz` backup before
any non-dry-run pass; `Curator.rollback/1` restores the latest.

```elixir
Raxol.Agent.Curator.run(dry_run: true)  # %{transitions: [...], backup: nil}
Raxol.Agent.Skills.Store.pin("rebase-onto-main", [])  # exempt from curation
```

Result: agents accumulate procedures during real work, promote the useful ones,
and let the unused ones decay -- without the operator hand-curating a skill
library. See [turn-memory.md](turn-memory.md) for the semantic-memory half of
the same after-turn write path.
