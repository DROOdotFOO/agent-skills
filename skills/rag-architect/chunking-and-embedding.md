---
title: Chunking and Embedding
impact: HIGH
impactDescription: Chunking strategy and embedding model selection guide for RAG pipelines
tags: rag, chunking, embeddings, text-splitting
---

# Chunking Strategies

## Fixed-Size

Split text into chunks of N tokens/characters with optional overlap.

- **Pros:** Simple, predictable chunk sizes, fast processing
- **Cons:** Breaks mid-sentence, ignores document structure, loses context at boundaries
- **Best for:** Homogeneous text, quick prototypes, baseline benchmarks
- **Parameters:** chunk_size (256-1024 tokens typical), overlap (10-20%)

## Sentence

Split on sentence boundaries using NLP sentence detection.

- **Pros:** Preserves sentence-level meaning, natural boundaries
- **Cons:** Uneven chunk sizes, single sentences may lack context
- **Best for:** Chat logs, social media, short-form content
- **Parameters:** sentences_per_chunk (3-5 typical), overlap (1-2 sentences)

## Paragraph

Split on paragraph boundaries (double newlines, blank lines).

- **Pros:** Preserves topic coherence, natural author-defined units
- **Cons:** Highly variable chunk sizes, some paragraphs too large or too small
- **Best for:** Blog posts, articles, essays with clear paragraph structure

## Semantic

Group text by semantic similarity using embeddings to detect topic shifts.

- **Pros:** Context-aware boundaries, groups related content regardless of formatting
- **Cons:** Requires embedding calls during chunking (cost), slower processing
- **Best for:** Code (AST-aware), transcripts, documents with poor formatting
- **Parameters:** similarity_threshold (0.7-0.85), min/max chunk size

## Recursive

Split by hierarchy of separators: paragraphs -> sentences -> words -> characters.

- **Pros:** Respects document structure, predictable sizes, good default
- **Cons:** Separator hierarchy may not match all document types
- **Best for:** General-purpose, technical documentation, markdown
- **Parameters:** separators list, chunk_size, overlap

## Document-Aware

Parse document structure (headings, sections, tables) and chunk by structural units.

- **Pros:** Preserves logical document structure, metadata-rich chunks
- **Cons:** Requires format-specific parsers, complex implementation
- **Best for:** Legal documents, medical records, structured reports, PDFs with sections
- **Parameters:** Format-specific (heading levels, section markers)

# Embedding Model Selection

## Dimension Considerations

| Dimensions | Tradeoff |
|-----------|----------|
| 128-256 | Fast, low storage. Good for simple similarity. Loses nuance. |
| 384-768 | Balanced. Good for most production use cases. |
| 1024-1536 | High quality. Better for complex queries. Higher cost/latency. |
| 2048+ | Diminishing returns for most tasks. Only for specialized domains. |

Rule of thumb: start with 768 dimensions. Only go higher if evaluation shows quality gaps.

## Speed vs Quality

- **Quantized models** -- 2-4x faster, ~1-3% quality loss. Use for high-throughput ingestion.
- **Distilled models** -- Smaller, faster, trained to mimic larger models. Good balance.
- **Full models** -- Highest quality, highest cost. Use when accuracy is critical.

## Categories

### General Purpose

- **Voyage AI (voyage-3)** -- 1024d, strong benchmark performance, good API
- **OpenAI (text-embedding-3-small/large)** -- 1536/3072d, widely supported, variable dimensions via Matryoshka
- **Cohere (embed-v3)** -- 1024d, built-in compression, search/classification modes
- **BGE (bge-large-en-v1.5)** -- 1024d, open-source, self-hostable

### Code-Specialized

- **Voyage Code (voyage-code-3)** -- Trained on code, understands syntax and semantics
- **CodeBERT / UniXcoder** -- Open-source, good for code search and similarity
- Best practice: include filename and language as metadata, not in the embedding text

### Scientific / Domain-Specific

- **SciBERT** -- Biomedical and scientific literature
- **Legal-BERT** -- Legal documents and case law
- Custom fine-tuned models for specialized vocabularies

### Multilingual

- **Cohere embed-multilingual-v3** -- 100+ languages, same quality across languages
- **BGE-M3** -- Open-source multilingual, supports dense + sparse + multi-vector
- Always test with target language data -- "multilingual" quality varies by language
