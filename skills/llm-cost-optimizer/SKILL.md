---
name: llm-cost-optimizer
description: >
  Analyze and reduce LLM API costs through model routing, caching, and prompt optimization.
  TRIGGER when: user asks about LLM costs, API spend reduction, token optimization, model routing, or prompt caching.
  DO NOT TRIGGER when: user asks about model quality comparison, fine-tuning, or general prompt engineering.
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: llm, cost-optimization, caching, routing, api
  license: MIT
---

# LLM Cost Optimizer

Reduce LLM API costs systematically without sacrificing output quality.

## Three Modes

### 1. Cost Audit

Assess current spend and find the 80/20 opportunities.

1. **Instrument** -- Add token counting and cost tracking per request. Log model, input tokens, output tokens, latency, and use case.
2. **Find 80/20** -- Identify which 20% of use cases drive 80% of cost. Sort by total spend, not per-request cost.
3. **Classify** -- Tag each use case by complexity: simple (classification, extraction), medium (summarization, Q&A), complex (reasoning, code generation, multi-step).

### 2. Optimize Existing

Apply techniques to reduce cost on current workloads.

1. **Routing** -- Route simple tasks to cheaper/smaller models. See optimization-techniques.md.
2. **Caching** -- Cache repeated or similar queries. Prompt caching for system prompts.
3. **Compression** -- Reduce prompt size without losing quality. Trim examples, remove redundancy.

### 3. Design Cost-Efficient

Build new systems with cost awareness from day one.

1. **Budget envelopes** -- Set per-feature monthly cost budgets. Alert at 80%.
2. **Routing layer** -- Default to cheapest model that meets quality bar. Escalate on failure.
3. **Observability** -- Track cost per user, per feature, per model. Dashboard with trends.

## Optimization Order

Apply techniques in this order (highest impact first):

1. Model routing (60-80% reduction potential)
2. Prompt caching (40-90% on cached portions)
3. Output length control (20-40%)
4. Prompt compression (15-30%)
5. Semantic caching (30-60% hit rate)
6. Request batching (10-25%)

See [optimization-techniques.md](./optimization-techniques.md) for detailed guidance on each technique.

## What You Get

- A cost audit identifying which use cases drive the majority of LLM spend, with per-request and total cost breakdowns.
- Prioritized optimization recommendations (model routing, caching, compression) ranked by reduction potential.
- Concrete implementation steps with expected cost savings percentages for each technique.

## Rules

1. Never optimize before measuring -- instrument first
2. Never sacrifice quality silently -- A/B test every change
3. Cost per request is misleading -- optimize total spend per outcome
4. The cheapest token is the one you never send
