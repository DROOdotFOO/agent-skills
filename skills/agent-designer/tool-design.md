---
title: Tool Design
impact: HIGH
impactDescription: Poorly designed tools cause agent failures, wasted tokens, and security vulnerabilities
tags: agents,tools,schema,error-handling,idempotency,validation
---

# Tool Design

Principles for designing tool interfaces that agents can use reliably.

## Schema Design Principles

### Clear naming

Tool names should be verb-noun: `read_file`, `search_code`, `create_issue`. Avoid ambiguous names like `process` or `handle`.

### Minimal parameters

Each tool should accept the fewest parameters needed. Required parameters only -- use sensible defaults for optional ones. Agents perform worse with tools that have 10+ parameters.

### Structured output

Return structured data (objects with named fields), not free-form text. The agent needs to parse the result programmatically for multi-step workflows.

```json
{
  "name": "search_code",
  "description": "Search for pattern matches in the codebase. Returns matching file paths and line numbers.",
  "parameters": {
    "type": "object",
    "required": ["pattern"],
    "properties": {
      "pattern": {
        "type": "string",
        "description": "Regex pattern to search for"
      },
      "file_glob": {
        "type": "string",
        "description": "Glob pattern to filter files (e.g. '*.ts'). Default: all files."
      },
      "max_results": {
        "type": "integer",
        "description": "Maximum matches to return. Default: 20."
      }
    }
  }
}
```

### Descriptive descriptions

The description is the agent's documentation. Include:
- What the tool does (one sentence)
- What it returns
- Constraints or side effects
- Example usage when non-obvious

## Error Handling Patterns

### Structured error payloads

Never return raw exception strings. Return a structured error the agent can reason about:

```json
{
  "error": {
    "code": "FILE_NOT_FOUND",
    "message": "File 'src/missing.ts' does not exist",
    "suggestion": "Use search_code to find the correct file path",
    "retryable": false
  }
}
```

### Error categories

| Category      | Retryable | Agent action                         |
|---------------|-----------|--------------------------------------|
| NOT_FOUND     | No        | Search for correct resource          |
| VALIDATION    | No        | Fix input parameters                 |
| RATE_LIMITED   | Yes       | Wait and retry (with backoff)       |
| TIMEOUT       | Yes       | Retry with smaller scope             |
| PERMISSION    | No        | Escalate to human or use alternative |
| INTERNAL      | Maybe     | Retry once, then escalate            |

### Fail loud, not silent

A tool that silently returns empty results when it fails is worse than one that returns an error. The agent cannot distinguish "no results found" from "search failed" unless the tool is explicit.

## Idempotency

Tools that modify state should be idempotent when possible: calling the tool twice with the same input should produce the same result, not double the side effect.

- `create_file` -- If file exists with same content, succeed silently. If different content, return conflict error.
- `add_label` -- If label already exists, succeed silently.
- `send_notification` -- Not naturally idempotent. Use a deduplication key parameter to prevent duplicate sends.

For non-idempotent tools, add a `dry_run` parameter so agents can preview the effect before committing.

## Input Validation

Validate at the tool boundary, not in the agent prompt:

- **Type checking** -- Reject wrong types before execution
- **Range checking** -- Bound numeric inputs (max file size, max results)
- **Format checking** -- Validate regex patterns, file paths, URLs before using them
- **Sanitization** -- Strip or reject inputs that could cause injection (shell commands, SQL, file traversal)

Return validation errors with the specific field and constraint that failed:

```json
{
  "error": {
    "code": "VALIDATION",
    "field": "max_results",
    "constraint": "Must be between 1 and 100",
    "received": 5000
  }
}
```

## Rate Limiting

Protect external tools from agent overuse:

- Set per-tool call limits (e.g., max 20 API calls per agent invocation)
- Implement token bucket or sliding window rate limiting
- Return `RATE_LIMITED` errors with `retry_after` hint
- Consider tool-level budgets: "this agent can spend at most $0.10 on external API calls"

## Tool Composition

When agents need multi-step tool use, design tools that compose cleanly:

- Output of tool A should be valid input for tool B without transformation
- Avoid tools that require the agent to parse unstructured output before passing to the next tool
- Consider composite tools for common sequences (e.g., `search_and_read` instead of requiring `search` then `read` for every lookup)
