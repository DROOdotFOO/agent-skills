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

1. **CLAUDE.md** (you write) -- Project-wide rules, preferences, conventions. Survives across all sessions.
2. **MEMORY.md** (Claude writes) -- Observations, patterns, corrections accumulated during sessions. Review candidates.
3. **Session Memory** -- In-context learnings that exist only for the current session. Lost on exit unless promoted.

## Commands

| Command | Action |
|---------|--------|
| `/si:review` | Scan MEMORY.md for promotion candidates. Show each with recurrence count and recommendation. |
| `/si:promote` | Promote a specific pattern from MEMORY.md to CLAUDE.md or `.claude/rules/`. Remove from MEMORY.md after promotion. |
| `/si:extract` | Generate a complete skill from a recurring pattern (creates `skills/<name>/SKILL.md`). |
| `/si:status` | Show memory stats: entries in MEMORY.md, staleness, promotion candidates, session observations. |
| `/si:remember` | Capture a specific observation to MEMORY.md with timestamp and context. |

## Promotion Lifecycle

See [promotion-lifecycle.md](./promotion-lifecycle.md) for detailed rules.

Summary: discover -> recurs 2-3x -> review flags -> promote to CLAUDE.md or rules -> remove from MEMORY.md.

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
- Promotion recommendations identifying recurring patterns ready to graduate to CLAUDE.md or `.claude/rules/`
- Extracted skills scaffolded from patterns that recur frequently enough to warrant standalone skill files

## Rules

1. Never promote after a single occurrence -- wait for recurrence
2. Always show the user what will be promoted and where before writing
3. Remove promoted entries from MEMORY.md to prevent duplication
4. Timestamp every MEMORY.md entry
5. Capture error patterns automatically (see promotion-lifecycle.md for error-capture hook)
