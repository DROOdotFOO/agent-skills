---
title: Evaluation Criteria
impact: CRITICAL
impactDescription: Wrong evaluation criteria lead to shallow, hard-to-use interfaces that leak implementation details
tags: design, evaluation, ousterhout, deep-modules, interface
---

# Evaluation Criteria

From Ousterhout's "A Philosophy of Software Design," adapted for interface comparison.

## Deep vs Shallow Modules

The single most important measure of interface quality.

**Deep module**: small, simple interface that hides significant implementation complexity. The caller gets powerful behavior with minimal cognitive load. Examples: Unix file I/O (5 syscalls, infinite complexity behind them), `HashMap.get()`.

**Shallow module**: interface that is nearly as complex as the implementation. The caller must understand internals to use it correctly. Every method does one trivial thing. Examples: Java's `InputStream` hierarchy, most "clean code" classes with one method each.

**Scoring**: count the number of public methods/types and compare to the amount of behavior they expose. Fewer methods with richer behavior = deeper = better.

## Simplicity of the Common Case

The most frequent usage pattern should require the fewest arguments, the least setup, and zero knowledge of edge cases. Optional parameters, sensible defaults, and progressive disclosure are tools.

**Scoring**: write the three most common usage examples. Count lines of code, number of concepts the caller must know, number of decisions the caller must make. Lower = better.

## Resistance to Misuse

A good interface makes incorrect usage difficult or impossible. Types, exhaustive enums, builder patterns, and "parse, don't validate" all contribute.

**Anti-patterns**: stringly-typed APIs, boolean parameters that are easy to swap, nullable returns where Result/Option would work, temporal coupling (must call A before B with no compiler enforcement).

**Scoring**: list the ways a caller could misuse the interface. Fewer = better. Compile-time enforcement beats runtime checks beats documentation.

## General-Purpose vs Specialized

General-purpose interfaces serve more callers but may sacrifice ergonomics for any single use case. Specialized interfaces are ergonomic for one caller but create proliferation.

**The sweet spot**: a general-purpose core with specialized convenience wrappers. The core handles all cases; the wrappers handle common cases with fewer arguments.

**Scoring**: count how many distinct use cases the interface serves without modification. More = better, unless the common case suffers.

## Implementation Efficiency

An interface that forces an inefficient implementation is a design bug, not an implementation problem. The interface shape constrains what algorithms are possible behind it.

**Example**: an interface that returns a full list when the caller only needs the first match forces O(n) work. An iterator/stream interface allows early termination.

**Scoring**: identify the performance-critical operations. Does the interface shape allow the optimal algorithm? If not, the interface is wrong.

## Comparison Matrix Template

| Criterion | Design A | Design B | Design C |
|-----------|----------|----------|----------|
| Depth (methods:behavior ratio) | | | |
| Common case simplicity (lines, concepts) | | | |
| Misuse resistance (misuse vectors) | | | |
| Generality (use cases served) | | | |
| Implementation efficiency | | | |
| **Overall** | | | |
