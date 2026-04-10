---
title: Common Pitfalls and Anti-Patterns
impact: HIGH
impactDescription: These mistakes cause silent failures, wasted retries, or broken integrations across all SDK languages.
tags: claude, api, pitfalls, anti-patterns, debugging, best-practices
---

# Common Pitfalls

## Input Handling

- Don't truncate inputs when passing files or content to the API. If the content is too long to fit in the context window, notify the user and discuss options (chunking, summarization, etc.) rather than silently truncating.

## Thinking & Effort

- **Opus 4.6 / Sonnet 4.6 thinking:** Use `thinking: {type: "adaptive"}` -- do NOT use `budget_tokens` (deprecated on both Opus 4.6 and Sonnet 4.6). For older models, `budget_tokens` must be less than `max_tokens` (minimum 1024). This will throw an error if you get it wrong.

## Prefill & Output

- **Opus 4.6 prefill removed:** Assistant message prefills (last-assistant-turn prefills) return a 400 error on Opus 4.6. Use structured outputs (`output_config.format`) or system prompt instructions to control response format instead.
- **Structured outputs (all models):** Use `output_config: {format: {...}}` instead of the deprecated `output_format` parameter on `messages.create()`. This is a general API change, not 4.6-specific.

## Token Limits

- **`max_tokens` defaults:** Don't lowball `max_tokens` -- hitting the cap truncates output mid-thought and requires a retry. For non-streaming requests, default to `~16000` (keeps responses under SDK HTTP timeouts). For streaming requests, default to `~64000` (timeouts aren't a concern, so give the model room). Only go lower when you have a hard reason: classification (`~256`), cost caps, or deliberately short outputs.
- **128K output tokens:** Opus 4.6 supports up to 128K `max_tokens`, but the SDKs require streaming for values that large to avoid HTTP timeouts. Use `.stream()` with `.get_final_message()` / `.finalMessage()`.

## JSON & Tool Calls

- **Tool call JSON parsing (Opus 4.6):** Opus 4.6 may produce different JSON string escaping in tool call `input` fields (e.g., Unicode or forward-slash escaping). Always parse tool inputs with `json.loads()` / `JSON.parse()` -- never do raw string matching on the serialized input.

## SDK Usage

- **Don't reimplement SDK functionality:** The SDK provides high-level helpers -- use them instead of building from scratch. Specifically: use `stream.finalMessage()` instead of wrapping `.on()` events in `new Promise()`; use typed exception classes (`Anthropic.RateLimitError`, etc.) instead of string-matching error messages; use SDK types (`Anthropic.MessageParam`, `Anthropic.Tool`, `Anthropic.Message`, etc.) instead of redefining equivalent interfaces.
- **Don't define custom types for SDK data structures:** The SDK exports types for all API objects. Use `Anthropic.MessageParam` for messages, `Anthropic.Tool` for tool definitions, `Anthropic.ToolUseBlock` / `Anthropic.ToolResultBlockParam` for tool results, `Anthropic.Message` for responses. Defining your own `interface ChatMessage { role: string; content: unknown }` duplicates what the SDK already provides and loses type safety.

## Code Execution

- **Report and document output:** For tasks that produce reports, documents, or visualizations, the code execution sandbox has `python-docx`, `python-pptx`, `matplotlib`, `pillow`, and `pypdf` pre-installed. Claude can generate formatted files (DOCX, PDF, charts) and return them via the Files API -- consider this for "report" or "document" type requests instead of plain stdout text.

## Cache

- **Silent cache invalidation:** Check `usage.cache_read_input_tokens`. If zero across repeated requests, a silent invalidator is at work. Common culprit: `datetime.now()` in system prompt. See `shared/prompt-caching.md` for the full audit checklist.
