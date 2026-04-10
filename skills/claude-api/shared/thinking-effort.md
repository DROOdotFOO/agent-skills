---
title: Thinking, Effort, and Compaction Reference
impact: CRITICAL
impactDescription: Incorrect thinking/effort config causes 400 errors (budget_tokens on 4.6) or wasted tokens (wrong effort level).
tags: claude, api, thinking, adaptive-thinking, effort, compaction, extended-thinking
---

# Thinking, Effort & Compaction

## Thinking

### Opus 4.6 -- Adaptive thinking (recommended)

Use `thinking: {type: "adaptive"}`. Claude dynamically decides when and how much to think. No `budget_tokens` needed -- `budget_tokens` is deprecated on Opus 4.6 and Sonnet 4.6 and must not be used. Adaptive thinking also automatically enables interleaved thinking (no beta header needed).

**When the user asks for "extended thinking", a "thinking budget", or `budget_tokens`:** always use Opus 4.6 with `thinking: {type: "adaptive"}`. The concept of a fixed token budget for thinking is deprecated -- adaptive thinking replaces it. Do NOT use `budget_tokens` and do NOT switch to an older model.

### Sonnet 4.6

Supports adaptive thinking (`thinking: {type: "adaptive"}`). `budget_tokens` is deprecated on Sonnet 4.6 -- use adaptive thinking instead.

### Older models (only if explicitly requested)

If the user specifically asks for Sonnet 4.5 or another older model, use `thinking: {type: "enabled", budget_tokens: N}`. `budget_tokens` must be less than `max_tokens` (minimum 1024). Never choose an older model just because the user mentions `budget_tokens` -- use Opus 4.6 with adaptive thinking instead.

---

## Effort

Controls thinking depth and overall token spend. GA, no beta header required.

```
output_config: {effort: "low" | "medium" | "high" | "max"}
```

- Goes inside `output_config`, not top-level
- Default is `high` (equivalent to omitting it)
- `max` is Opus 4.6 only
- Works on Opus 4.5, Opus 4.6, and Sonnet 4.6
- Will error on Sonnet 4.5 / Haiku 4.5
- Combine with adaptive thinking for the best cost-quality tradeoffs
- Use `low` for subagents or simple tasks; `max` for the deepest reasoning

---

## Compaction

**Beta, Opus 4.6 and Sonnet 4.6.** For long-running conversations that may exceed the 200K context window, enable server-side compaction. The API automatically summarizes earlier context when it approaches the trigger threshold (default: 150K tokens). Requires beta header `compact-2026-01-12`.

**Critical:** Append `response.content` (not just the text) back to your messages on every turn. Compaction blocks in the response must be preserved -- the API uses them to replace the compacted history on the next request. Extracting only the text string and appending that will silently lose the compaction state.

See `{lang}/claude-api/README.md` (Compaction section) for code examples. Full docs via WebFetch in `shared/live-sources.md`.
