---
title: Promotion Lifecycle
impact: HIGH
impactDescription: Rules for when and where to promote patterns from session memory to permanent configuration
tags: memory, promotion, patterns, automation
---

# Promotion Lifecycle

## When to Promote

A pattern is a promotion candidate when ALL of these are true:

- **Recurrence** -- The pattern has been observed 2-3+ times across different contexts (not just repeated in one session)
- **Multi-file impact** -- It affects multiple files, modules, or sessions (not isolated to one spot)
- **Time savings** -- Promoting it would save significant time in future sessions (avoids repeated corrections)

A pattern is NOT ready for promotion when:

- It occurred only once (could be situational)
- It applies only to a single file or function
- The user hasn't confirmed the preference (for subjective choices)

## Where to Promote

### CLAUDE.md (project-wide rules)

Best for: coding conventions, tool preferences, workflow patterns, architectural decisions.

Examples:
- "Always use `pathlib` over `os.path` in Python"
- "Run `make lint` before committing"
- "Prefer composition over inheritance in this codebase"

### .claude/rules/ (context-specific)

Best for: patterns that apply only in certain directories, file types, or situations. Rules files support glob patterns for automatic activation.

Examples:
- `*.test.ts` -- "Always use `describe`/`it` blocks, never standalone `test()`"
- `src/api/**` -- "All endpoints must validate input with zod"

### Skill extraction (reusable across projects)

Best for: patterns general enough to apply across multiple projects. When a pattern transcends the current codebase, extract it as a standalone skill.

Criteria for skill extraction:
- Not specific to this project's domain
- Would benefit any project in the same language/framework
- Complex enough to warrant its own documentation

## Agents

### Memory Analyst

Runs during `/si:review`. Responsibilities:

- **Identify candidates** -- Scan MEMORY.md for entries with recurrence count >= 2
- **Flag stale entries** -- Entries older than 30 days without recurrence are candidates for removal
- **Detect gaps** -- Compare CLAUDE.md rules against recent session corrections. Missing rules that keep getting corrected are promotion candidates.
- **Deduplicate** -- Find entries that describe the same pattern in different words

### Skill Extractor

Runs during `/si:extract`. Responsibilities:

- Generate a complete skill directory with SKILL.md and sub-files
- Include proper frontmatter (name, description with TRIGGER/DO NOT TRIGGER, metadata)
- Populate sub-files with detailed patterns, examples, and anti-patterns
- Validate with `./scripts/skills-lint.sh` if available

## Error-Capture Hook

Automatic pattern capture on tool errors. Configured as a PostToolUse hook on Bash:

- Triggers only on non-zero exit codes
- Captures ~30 tokens maximum (command + error summary)
- Appends to MEMORY.md under `## Error Patterns` with timestamp
- Does NOT interrupt the user's workflow
- Groups repeated errors (increments count instead of duplicating)

Format:
```markdown
## Error Patterns

- [2026-04-05] `cargo build` -> missing feature flag `serde` (seen 2x)
- [2026-04-07] `npm test` -> jest config not found in monorepo subfolder (seen 1x)
```

## Promotion Checklist

Before promoting, verify:

1. [ ] Pattern recurred 2+ times
2. [ ] User confirmed the preference (if subjective)
3. [ ] Target location identified (CLAUDE.md / rules / skill)
4. [ ] No existing rule covers this pattern
5. [ ] Wording is clear and actionable
6. [ ] Entry removed from MEMORY.md after promotion
