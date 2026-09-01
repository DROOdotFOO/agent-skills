---
name: self-improving-agent
description: >
  Auto-curate memory, promote recurring patterns, and extract reusable knowledge across sessions.
  TRIGGER when: user says "/si:", asks about memory management, pattern promotion, or wants to review accumulated learnings.
  DO NOT TRIGGER when: user wants general code review, documentation, or project planning.
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: memory, self-improvement, patterns, automation, meta-cognition
  license: MIT
---

# Self-Improving Agent

Curate session memory, promote recurring patterns to permanent config, and extract reusable skills.

## Memory Stack

Three tiers, from most permanent to most ephemeral:

1. **Repository guidance** (you write) -- AGENTS.md in Codex or CLAUDE.md in Claude Code. Project-wide rules, preferences, and conventions that survive across sessions.
2. **Review memory** -- The host memory store, or a project MEMORY.md when the user has chosen a file-backed ledger. Observations, patterns, and corrections awaiting review.
3. **Session Memory** -- In-context learnings that exist only for the current session. Lost on exit unless promoted.

## Commands

| Command | Action |
|---------|--------|
| `review` | Scan the active review-memory source for promotion candidates. Show each with recurrence count and recommendation. |
| `promote` | Promote a pattern to AGENTS.md, CLAUDE.md, or an appropriate scoped rule. Remove it from review memory after promotion. |
| `extract` | Generate a complete skill from a recurring pattern (creates `skills/<name>/SKILL.md`). |
| `status` | Show memory stats: entries, staleness, promotion candidates, and session observations. |
| `remember` | Capture a specific observation with timestamp and context. |

Invoke these as `$self-improving-agent <command>` in Codex, `/si:<command>` in
Claude Code, or describe the operation in natural language.

## Promotion Lifecycle

See [promotion-lifecycle.md](./promotion-lifecycle.md) for detailed rules.

Summary: discover -> recurs 2-3x -> review flags -> promote to durable host guidance or a skill -> remove from review memory.

## MEMORY.md Format

```markdown
## Patterns

- [2026-04-01] Always use `--no-ff` for feature merges (seen 3x)
- [2026-04-03] Tests fail silently when DB not running -- add health check (seen 2x)

## Corrections

- [2026-04-02] User prefers `Result<T>` over panics in Rust (corrected 1x)

## Observations

- [2026-04-05] Build takes 4min -- investigate caching
```

## What You Get

- A curated MEMORY.md with timestamped patterns, corrections, and observations accumulated across sessions
- Promotion recommendations identifying recurring patterns ready to graduate to AGENTS.md, CLAUDE.md, scoped rules, or a reusable skill
- Extracted skills scaffolded from patterns that recur frequently enough to warrant standalone skill files

## Rules

1. Never promote after a single occurrence -- wait for recurrence
2. Always show the user what will be promoted and where before writing
3. Remove promoted entries from MEMORY.md to prevent duplication
4. Timestamp every MEMORY.md entry
5. Capture error patterns automatically (see promotion-lifecycle.md for error-capture hook)
