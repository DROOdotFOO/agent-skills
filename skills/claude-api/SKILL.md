---
name: claude-api
description: >
  Build apps with the Claude API or Anthropic SDK.
  TRIGGER when: code imports `anthropic`/`@anthropic-ai/sdk`/`claude_agent_sdk`,
  or user asks to use Claude API, Anthropic SDKs, or Agent SDK.
  DO NOT TRIGGER when: code imports `openai`/other AI SDK, general programming,
  or ML/data-science tasks.
metadata:
  author: anthropic
  version: "1.0.0"
  tags: claude, api, sdk, anthropic, agent-sdk, llm, tool-use
  license: MIT
---

# Building LLM-Powered Applications with Claude

Choose the right surface, detect the project language, read the relevant docs.

## What You Get

- Language-detected SDK examples (Python, TypeScript, Go, Elixir, Rust, Lua, cURL)
- Decision tree: single call vs workflow vs agent vs Agent SDK
- Current model IDs, thinking/effort config, caching patterns
- Tool use patterns (tool runner, manual loop, code execution)
- Error taxonomy and live documentation URLs

## Top Pitfalls (quick reference)

| Mistake                                         | Fix                                                                                      |
| ----------------------------------------------- | ---------------------------------------------------------------------------------------- |
| Using `budget_tokens` on Opus 4.6 / Sonnet 4.6  | Use `thinking: {type: "adaptive"}` -- budget_tokens is deprecated                        |
| Lowballing `max_tokens`                         | Default ~16K non-streaming, ~64K streaming. Truncation = wasted retry                    |
| Prefilling assistant message on Opus 4.6        | Returns 400. Use structured outputs or system prompt instead                             |
| Silent cache invalidation                       | Check `usage.cache_read_input_tokens`. Common culprit: `datetime.now()` in system prompt |
| Redefining SDK types                            | Use `Anthropic.MessageParam`, `Anthropic.Tool`, etc. -- don't roll your own              |

Full list: `shared/pitfalls.md`

## Defaults

Use **Claude Opus 4.6** (`claude-opus-4-6`) unless the user names a different model. Use **adaptive thinking** (`thinking: {type: "adaptive"}`) for anything remotely complicated. Use **streaming** for long input/output -- `.get_final_message()` / `.finalMessage()` if you don't need individual events.

## Language Detection

Infer from project files:

- `*.py`, `pyproject.toml`, `requirements.txt` -> **Python** -- read from `python/`
- `*.ts`, `*.tsx`, `package.json`, `tsconfig.json` -> **TypeScript** -- read from `typescript/`
- `*.js`, `*.jsx` (no `.ts` present) -> **TypeScript** -- JS uses the same SDK
- `*.go`, `go.mod` -> **Go** -- read from `go/`
- `*.ex`, `*.exs`, `mix.exs` -> **Elixir** -- read from `elixir/`
- `*.rs`, `Cargo.toml` -> **Rust** -- read from `rust/`
- `*.lua`, `.luarc.json` -> **Lua** -- read from `lua/`

If ambiguous, ask. If unsupported language, suggest `curl/` examples.

## Which Surface?

| Use Case                          | Surface                   |
| --------------------------------- | ------------------------- |
| Single call (classify, summarize) | Claude API                |
| Multi-step pipeline, your tools   | Claude API + tool use     |
| Agent needing file/web/terminal   | Agent SDK                 |
| Custom agent, your own tools      | Claude API agentic loop   |

Decision tree and "Should I Build an Agent?" criteria: `shared/surfaces.md`

## Reading Guide

| Task | Read |
| ---- | ---- |
| Single call (classify/summarize/extract) | `{lang}/claude-api/README.md` |
| Chat UI / streaming | + `{lang}/claude-api/streaming.md` |
| Long conversations (context overflow) | + Compaction section; details: `shared/thinking-effort.md` |
| Prompt caching / cache optimization | `shared/prompt-caching.md` + `{lang}/claude-api/README.md` |
| Tool use / function calling / agents | + `shared/tool-use-concepts.md` + `{lang}/claude-api/tool-use.md` |
| Batch processing | + `{lang}/claude-api/batches.md` |
| File uploads across requests | + `{lang}/claude-api/files-api.md` |
| Agent with built-in tools | `{lang}/agent-sdk/README.md` + `{lang}/agent-sdk/patterns.md` |
| Model selection / capabilities | `shared/models.md` |
| Thinking, effort, compaction | `shared/thinking-effort.md` |
| Error handling | `shared/error-codes.md` |

> Go, Elixir, Rust, Lua, cURL: single file covers all basics. Read that plus `shared/` files as needed.

## When to Use WebFetch

Use when user asks for "latest" info, cached data seems wrong, or features aren't covered here. URLs: `shared/live-sources.md`.
