---
title: Optimization Techniques
impact: CRITICAL
impactDescription: LLM cost reduction techniques in priority order with implementation guidance and anti-patterns
tags: llm, cost-optimization, routing, caching, batching
---

# Optimization Techniques

Apply in priority order. Each section includes reduction potential and implementation notes.

## 1. Model Routing (60-80% reduction)

Route requests to the cheapest model that meets quality requirements.

**Implementation:**
- Classify requests by complexity using a lightweight classifier (regex, keyword, or small model)
- Simple tasks (classification, extraction, formatting): use Haiku-class models
- Medium tasks (summarization, Q&A, translation): use Sonnet-class models
- Complex tasks (reasoning, code generation, multi-step analysis): use Opus-class models

**Routing signals:**
- Input length (short inputs rarely need large models)
- Task type (extractable from system prompt or API endpoint)
- Required output quality (user-facing vs internal)
- Fallback: if small model confidence is low, retry with larger model

**Cost comparison (approximate, per 1M tokens input):**
- Haiku-class: $0.25-0.80
- Sonnet-class: $3.00
- Opus-class: $15.00

## 2. Prompt Caching (40-90% on cached portions)

Cache static prompt prefixes to avoid reprocessing on every request.

**Anthropic cache_control:**
```json
{
  "system": [
    {
      "type": "text",
      "text": "Your large system prompt here...",
      "cache_control": {"type": "ephemeral"}
    }
  ]
}
```

- Cached tokens cost 90% less on cache hits (Anthropic pricing)
- Cache lives for 5 minutes, refreshed on each hit
- Place `cache_control` breakpoints at stable content boundaries
- Best ROI when system prompt is large (>1024 tokens) and reused frequently

**What to cache:**
- System prompts (highest ROI)
- Few-shot examples
- Reference documentation included in context
- Tool definitions

## 3. Output Length Control (20-40% reduction)

Reduce output tokens by setting appropriate `max_tokens` and instructing conciseness.

**Techniques:**
- Set `max_tokens` to expected output size + 20% buffer (not the model maximum)
- Add explicit length instructions: "Respond in 2-3 sentences" or "Return only the JSON object"
- Use structured output (JSON mode) to eliminate prose wrapping
- For classification tasks: constrain to enum values only

**Common waste:**
- Default max_tokens left at 4096 when 200 would suffice
- Model generating explanations when only a value is needed
- Redundant preambles ("Sure, I'd be happy to help...")

## 4. Prompt Compression (15-30% reduction)

Reduce input tokens without losing information.

**Techniques:**
- Remove redundant instructions (say it once, not three times)
- Compress few-shot examples to minimum viable demonstrations
- Use references instead of repetition ("same format as above")
- Strip unnecessary whitespace, comments, and formatting in code contexts
- Summarize long documents before including as context

**Caution:** Always A/B test compression against quality. Aggressive compression degrades output.

## 5. Semantic Caching (30-60% hit rate)

Cache responses and return them for semantically similar queries.

**Implementation:**
- Embed each query, store with response in vector DB
- On new query, check vector similarity against cache
- Return cached response if similarity > threshold (0.92-0.95 typical)
- Set TTL based on content volatility (static content: days, dynamic: minutes)

**Best for:**
- Customer support (many users ask the same questions differently)
- Documentation Q&A (finite question space)
- Code explanation (same code, different phrasings)

**Not suitable for:**
- Creative tasks (each response should be unique)
- Personalized responses (user context matters)
- Real-time data queries (answers change)

## 6. Request Batching (10-25% reduction)

Batch multiple requests into single API calls.

**Anthropic Message Batches API:**
- Submit up to 10,000 requests per batch
- 50% cost reduction on batched requests
- Results available within 24 hours
- Best for: non-real-time processing, bulk analysis, data labeling

**When to batch:**
- Processing document collections
- Generating embeddings for ingestion
- Bulk classification or extraction
- Any workflow where latency tolerance > minutes

## 7. Cross-Agent Context Management (20-50% reduction)

Manage how much context flows between agents in multi-step pipelines. In hierarchical architectures (orchestrator + workers), token usage compounds across calls as context gets passed repeatedly.

**Relevance-floor filtering:**
- Don't return all results up to a fixed `limit`. Apply a relevance floor that adapts to the score distribution.
- Use MAD-normalized thresholding: keep items where `score > median + threshold * MAD` (median absolute deviation). This adapts to each query's score distribution automatically.
- threshold=0.0 keeps above-median items. threshold=1.0 keeps only clear outliers. Tune per use case.

**Task-guided selection:**
- Before assembling context for a downstream agent, score each context item against the consumer's task description.
- Simple approach: count term overlap between task description and context items, boost matches.
- Advanced approach (requires model access): use attention patterns between task query and context to select relevant positions (see Latent Briefing, Ramp Labs).

**Adaptive budget by task type:**
- Focused tasks (bug fix, specific question) need less context -- aggressive filtering improves signal-to-noise.
- Broad tasks (architecture review, onboarding) need more context -- light filtering preserves coverage.
- Set token budgets per task type: bug fix ~1500 tokens, feature work ~3000, architecture review ~5000+.

**Implementation priority:**
1. Add relevance floors to existing search/retrieval (quick win, no new infrastructure)
2. Add token budgets to context assembly functions
3. Add task-hint parameters for consumer-aware filtering

**Reference:** Latent Briefing (Ramp Labs, 2026) demonstrates these patterns at the representation level using KV cache compaction, achieving 42-57% token reduction with +3pp accuracy on LongBench v2.

# Proactive Triggers

Surface these optimizations proactively when you observe these patterns (do not wait to be asked):

1. **Large system prompt reused across requests** -> Suggest prompt caching
2. **Same model used for all tasks regardless of complexity** -> Suggest model routing
3. **max_tokens set to model maximum on simple tasks** -> Suggest output length control
4. **Repeated similar queries in logs** -> Suggest semantic caching
5. **Batch processing done sequentially** -> Suggest request batching API
6. **No cost tracking or observability** -> Suggest instrumentation first
7. **Context assembled for multi-agent pipeline without relevance filtering** -> Suggest cross-agent context management

# Anti-Patterns

| Anti-Pattern | Problem | Better Approach |
|-------------|---------|-----------------|
| Using Opus for everything | 15-60x more expensive than Haiku | Route by complexity |
| Caching without TTL | Stale responses, wrong answers | Always set TTL based on content volatility |
| Optimizing before measuring | Solving wrong problem | Instrument, find 80/20, then optimize |
| Compressing prompts aggressively | Quality degrades silently | A/B test every compression change |
| Ignoring output tokens | Output often costs 3-5x more per token | Control output length explicitly |
| Building custom cache before trying provider caching | Unnecessary complexity | Use Anthropic prompt caching first |
| Retrying on larger model without logging | Hidden cost multiplier | Log escalations, track escalation rate |
| Passing all context between agents | Token explosion, accuracy dilution | Filter by relevance floor + task budget |
