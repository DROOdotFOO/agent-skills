---
title: Dependency Classification
impact: CRITICAL
impactDescription: Categorize dependencies by type, calculate coupling scores, detect circular dependencies and shallow modules
tags: dependencies, coupling, architecture, anti-patterns
---

# Dependency Classification

## Four dependency types

Every dependency in a system falls into one of four categories. The type
determines the coupling risk and the mitigation strategy.

### 1. In-process (same binary)

Direct function/method calls within the same compiled artifact. Shared memory,
shared types, shared lifecycle.

- **Coupling risk**: HIGH -- changes propagate at compile time
- **Mitigation**: interfaces/traits at module boundaries, dependency inversion
- **Examples**: service calling a repository, handler calling a use case

### 2. Local-subprocess (child process)

Your code spawns and manages the process. Communication via stdin/stdout,
pipes, or local sockets. You control the lifecycle.

- **Coupling risk**: MEDIUM -- protocol coupling, lifecycle coupling
- **Mitigation**: well-defined protocols (JSON-RPC, protobuf), health checks
- **Examples**: worker processes, language server, sidecar tools

### 3. Remote-owned (your team's service)

Network call to a service your team deploys and maintains. You control both
sides but they deploy independently.

- **Coupling risk**: MEDIUM -- API versioning, network failure
- **Mitigation**: contract testing, backward-compatible APIs, circuit breakers
- **Examples**: internal microservices, internal APIs, shared databases

### 4. True-external (third-party API)

Network call to a service you do not control. API can change, rate limits
apply, downtime is outside your control.

- **Coupling risk**: HIGH -- no control over availability or API stability
- **Mitigation**: anti-corruption layer, caching, fallback behavior, retries
- **Examples**: Stripe API, GitHub API, cloud provider SDKs

## Coupling score calculation

For each dependency, score on three axes (1-5 each):

| Axis | 1 (low) | 5 (high) |
|------|---------|----------|
| **Frequency** | Rarely called | Called on every request |
| **Breadth** | One call site | Many call sites across modules |
| **Replaceability** | Swap with config change | Rewrite required |

**Coupling score** = Frequency + Breadth + Replaceability (range: 3-15)

- 3-6: Low coupling -- acceptable
- 7-10: Medium coupling -- consider abstraction boundary
- 11-15: High coupling -- requires interface/anti-corruption layer

## Circular dependency detection

Circular dependencies are always an anti-pattern. Detection process:

1. Build a directed graph of module imports/dependencies
2. Run topological sort -- cycles will be detected as failures
3. For each cycle, identify the weakest edge (lowest semantic coupling)
4. Recommend breaking at the weakest edge by extracting a shared interface

Common cycle-breaking strategies:
- Extract shared types into a common module
- Invert the dependency via callback/event
- Merge the two modules (if they are really one concept)

## Shallow module identification

A shallow module has a large interface relative to its implementation. It adds
ceremony without hiding complexity.

**Indicators**:
- Public API surface > 2x the private implementation logic
- Most methods are simple pass-throughs to another module
- Removing the module and calling the underlying code directly would simplify
  callers

**Action**: Either deepen the module (add real logic/policy) or inline it.
