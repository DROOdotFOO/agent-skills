---
title: Guardrails
impact: CRITICAL
impactDescription: Missing guardrails allow agents to take harmful actions, leak data, or run indefinitely
tags: agents,guardrails,safety,memory,evaluation,human-in-the-loop
---

# Guardrails

Safety mechanisms, memory management, failure handling, and evaluation frameworks for agent systems.

## Input Validation

Validate everything entering the agent system:

- **Prompt injection detection** -- Scan user inputs for attempts to override system instructions. Reject or sanitize before passing to agents.
- **Context length limits** -- Truncate or summarize inputs exceeding the context window. Agents degrade silently when context overflows.
- **Schema validation** -- When agents receive structured input from other agents, validate against the expected schema before processing.
- **Sensitive data filtering** -- Strip PII, credentials, and secrets from inputs before they enter agent context. Use allowlists, not blocklists.

## Output Filtering

Validate everything leaving the agent system:

- **Format validation** -- Verify outputs match expected schema before returning to user or passing to next agent.
- **Content filtering** -- Check for leaked system prompts, internal tool names, or sensitive data in outputs.
- **Hallucination markers** -- Flag outputs that reference files, URLs, or data the agent did not actually retrieve via tools.
- **Action validation** -- For agents that take actions (write files, send messages, create resources), validate the action against an allowlist before executing.

## Human-in-the-Loop Gates

Insert approval checkpoints for high-risk operations:

| Risk level | Gate type        | Examples                                    |
|------------|------------------|---------------------------------------------|
| LOW        | No gate          | Read-only operations, search, analysis      |
| MEDIUM     | Audit log        | File writes, config changes (log, no block) |
| HIGH       | Approval prompt  | External API calls, data deletion, payments |
| CRITICAL   | Multi-party      | Production deploys, access grants, PII ops  |

Design gates to be non-blocking where possible: queue the action, notify the human, continue other work while waiting for approval.

## Memory Patterns

### Short-term memory

The current conversation context. Limited by context window. Use summarization to compress older turns.

### Long-term memory

Persistent storage across sessions:

- **Vector store** -- Embed and retrieve relevant past interactions, documents, code snippets
- **Structured store** -- Key-value or relational database for facts, preferences, project state
- **File system** -- Markdown files, scratch pads, intermediate results

### Shared memory

For multi-agent systems, shared memory enables coordination:

- **Shared scratchpad** -- All agents read/write to a common document
- **Message queue** -- Agents post findings that others can consume
- **State machine** -- Shared state object with transitions controlled by the orchestrator

Design shared memory with clear ownership: who can write to each section, and what happens on conflicting writes.

## Failure Handling

### Retry with backoff

For transient failures (API timeouts, rate limits):

```
Attempt 1: immediate
Attempt 2: wait 1s
Attempt 3: wait 4s
Max retries: 3
```

### Fallback

When a tool or agent fails permanently:

- **Alternative tool** -- Try a different tool that achieves the same goal (e.g., web search instead of docs search)
- **Degraded mode** -- Return partial results with a disclaimer about what is missing
- **Human escalation** -- Surface the failure to a human with context about what was attempted

### Circuit breaker

If an agent or tool fails repeatedly, stop calling it:

- **Open** -- After 3 consecutive failures, stop calling for 5 minutes
- **Half-open** -- After cooldown, allow one probe call
- **Closed** -- If probe succeeds, resume normal operation

Prevent cascade failures: if agent B depends on agent A, and A is circuit-broken, do not let B retry indefinitely.

### Timeout enforcement

Set timeouts at every level:

- Per tool call: 30 seconds
- Per agent turn: 2 minutes
- Per pipeline: 10 minutes
- Per user request: 15 minutes

Kill and report on timeout rather than hanging indefinitely.

## Evaluation Frameworks

Measure agent system quality across four dimensions:

### Task completion

- **Success rate** -- Percentage of tasks completed correctly
- **Partial completion** -- When full completion fails, how much was achieved?
- **Error classification** -- Why did failures occur? (tool failure, wrong plan, hallucination, timeout)

### Quality

- **Correctness** -- Are the outputs factually accurate and logically sound?
- **Relevance** -- Do outputs address the actual question, not a related one?
- **Completeness** -- Are all parts of the task addressed?

### Cost

- **Token usage** -- Input + output tokens per task
- **Tool calls** -- Number of external API calls per task
- **Dollar cost** -- Total spend per task (LLM + tools + infrastructure)
- **Cost per quality point** -- Normalize cost by quality score to compare approaches

### Latency

- **End-to-end** -- Total time from request to response
- **Time to first token** -- How long before the user sees any output?
- **Agent idle time** -- Time spent waiting for tools vs reasoning
- **Parallelism efficiency** -- For multi-agent systems, how much wall-clock time is saved by parallel execution?

Build evaluation datasets from real usage. Synthetic benchmarks measure the wrong thing.
