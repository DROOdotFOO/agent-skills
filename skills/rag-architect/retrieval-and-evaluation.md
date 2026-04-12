---
title: Retrieval and Evaluation
impact: CRITICAL
impactDescription: Retrieval strategies, vector DB selection, evaluation metrics, and production patterns for RAG
tags: rag, retrieval, vector-db, evaluation, production
---

# Retrieval Strategies

## Dense Retrieval

Embed query, find nearest neighbors in vector space.

- **Pros:** Captures semantic meaning, handles paraphrases
- **Cons:** Misses exact keyword matches, struggles with rare terms
- **When:** General semantic search, conversational queries

## Sparse Retrieval

Traditional keyword matching (BM25, TF-IDF).

- **Pros:** Exact term matching, handles rare/technical terms, fast, no embedding cost
- **Cons:** Misses semantic similarity, brittle to paraphrasing
- **When:** Keyword-heavy queries, technical documentation, known-item search

## Hybrid (Dense + Sparse)

Combine dense and sparse scores. Use Reciprocal Rank Fusion (RRF) to merge ranked lists.

- **Pros:** Best of both worlds, robust across query types
- **Cons:** More complex, two retrieval paths to maintain
- **When:** Production systems (almost always the right choice)
- **RRF formula:** `score = sum(1 / (k + rank_i))` where k=60 is standard

## Reranking

Retrieve top-N candidates with fast retrieval, then rerank with a cross-encoder.

- **Pros:** Significantly improves precision, catches retrieval errors
- **Cons:** Adds latency (50-200ms), cost per query, limited to reranking top-N
- **When:** Accuracy-critical applications, after initial retrieval returns 20-100 candidates
- **Models:** Cohere Rerank, Voyage Rerank, cross-encoder/ms-marco-MiniLM-L-6-v2 (open-source)

# Query Transformation

## HyDE (Hypothetical Document Embeddings)

Generate a hypothetical answer, embed that instead of the query. The hypothetical answer is closer in embedding space to actual answers than the question is.

- **Best for:** Questions where the query and answer have very different vocabulary

## Multi-Query

Generate 3-5 query variations, retrieve for each, deduplicate results.

- **Best for:** Ambiguous queries, broad topics, improving recall

## Step-Back Prompting

Abstract the query to a higher-level question first, retrieve for both.

- **Best for:** Specific questions that need broader context ("What was the GDP of France in 2023?" -> also retrieve "French economic indicators")

# Vector DB Selection

| DB           | Best For                | Hosting               | Key Features                                    |
| ------------ | ----------------------- | --------------------- | ----------------------------------------------- |
| **Pinecone** | Managed, zero-ops       | Cloud only            | Serverless tier, metadata filtering, namespaces |
| **Weaviate** | Hybrid search           | Cloud + self-host     | Built-in BM25 + vector, GraphQL API, modules    |
| **Qdrant**   | Performance, filtering  | Cloud + self-host     | Rich filtering, quantization, gRPC, Rust-based  |
| **Chroma**   | Prototyping, local dev  | Embedded + cloud      | Simple API, Python-native, lightweight          |
| **pgvector** | Existing Postgres users | Self-host (extension) | SQL interface, ACID, joins with relational data |

Decision factors:

- **Scale:** < 1M vectors -> any DB works. > 10M -> Pinecone, Qdrant, or Weaviate.
- **Filtering:** Complex metadata filters -> Qdrant or Weaviate. Simple -> any.
- **Ops budget:** Zero -> Pinecone serverless or Chroma cloud. Have infra team -> self-host Qdrant.
- **Existing stack:** Already on Postgres -> pgvector. Already on K8s -> Qdrant/Weaviate.

# Evaluation

## Core Metrics

| Metric                | Target | Measures                                                |
| --------------------- | ------ | ------------------------------------------------------- |
| **Faithfulness**      | > 90%  | Are generated answers grounded in retrieved context?    |
| **Answer Relevance**  | > 0.85 | Does the answer address the question?                   |
| **Context Precision** | > 0.80 | Are relevant chunks ranked higher than irrelevant ones? |
| **Context Recall**    | > 0.75 | Are all necessary chunks retrieved?                     |

## RAGAS Framework

Use RAGAS for automated RAG evaluation:

- Faithfulness: LLM judges if each claim in the answer is supported by context
- Answer relevance: LLM generates questions from the answer, measures similarity to original
- Context precision/recall: Compare retrieved chunks against ground-truth relevant chunks

## Evaluation Dataset

Minimum 50-100 question-answer pairs with ground-truth context. Include:

- Simple factual questions (baseline)
- Multi-hop questions (tests chunk linking)
- Questions with no answer in corpus (tests abstention)
- Adversarial questions (tests guardrails)

# Production Patterns

## Caching

- **Query-level cache** -- Exact match on query string. Fast, high hit rate for repeated queries. Use Redis/Memcached with TTL.
- **Semantic cache** -- Embed the query, check vector similarity against cached queries. Catches paraphrases. Higher overhead but better hit rate.

## Streaming

Stream the LLM response while retrieval runs. Show "searching..." indicator, then stream generation. Reduces perceived latency.

## Fallback

When retrieval returns low-confidence results (similarity < threshold):

1. Try query expansion (multi-query)
2. Fall back to broader search (remove filters)
3. Respond with "I don't have enough information" rather than hallucinating

# Cost Optimization

- **Batch embedding** -- Embed documents in batches, not one at a time. Most APIs support batch endpoints.
- **Quantization** -- Use scalar/binary quantization in vector DB. Reduces storage 4-32x with minimal quality loss.
- **Tiered storage** -- Hot tier for recent/frequent documents, cold tier for archive. Move based on access patterns.
- **Query routing** -- Simple queries use smaller/cheaper models. Complex queries use full pipeline.

# Guardrails

- **Content filtering** -- Check retrieved chunks for harmful content before passing to LLM
- **PII detection** -- Scan chunks for PII before including in context. Redact or exclude.
- **Injection prevention** -- Sanitize retrieved text to prevent prompt injection via poisoned documents
- **Source attribution** -- Always include chunk sources in responses for verifiability
