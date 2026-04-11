---
name: rag-architect
description: >
  Design RAG pipelines with informed chunking, embedding, retrieval, and evaluation decisions.
  TRIGGER when: user asks about RAG pipeline design, chunking strategies, embedding models, vector databases, or retrieval-augmented generation.
  DO NOT TRIGGER when: user asks about fine-tuning, prompt engineering without retrieval, or general LLM usage.
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: rag, embeddings, vector-db, retrieval, chunking, llm
  license: MIT
---

# RAG Architect

Design retrieval-augmented generation pipelines with the right tradeoffs at each layer.

## Workflow

1. **Choose chunking strategy** -- Match chunk method to document structure
2. **Select embedding model** -- Balance dimensions, speed, and domain fit
3. **Choose vector DB** -- Match scale, features, and deployment model
4. **Design retrieval** -- Dense, sparse, hybrid, or reranked
5. **Evaluate** -- Measure faithfulness, relevance, and answer quality

## Reading Guide

| Decision | File |
|----------|------|
| Chunking strategies + embedding models | [chunking-and-embedding.md](./chunking-and-embedding.md) |
| Retrieval strategies + vector DBs + evaluation | [retrieval-and-evaluation.md](./retrieval-and-evaluation.md) |

## Quick Decision Matrix

| Document type | Chunking | Embedding | Retrieval |
|---------------|----------|-----------|-----------|
| Code | Semantic (AST-aware) | Code-specialized | Hybrid + rerank |
| Legal/medical | Document-aware (sections) | Domain-specific | Dense + rerank |
| Chat logs | Sentence | General-purpose | Dense |
| Technical docs | Recursive | General-purpose | Hybrid |
| Mixed/unknown | Recursive (fallback) | General-purpose | Hybrid + rerank |

## Rules

1. Start simple -- fixed-size chunks + dense retrieval is a valid baseline
2. Measure before optimizing -- run RAGAS evaluation before adding complexity
3. Chunk overlap matters -- 10-20% overlap prevents context loss at boundaries
4. Embedding dimensions are a tradeoff -- higher is not always better (cost, latency)
5. Hybrid retrieval (dense + sparse) almost always beats either alone
