---
title: Deep Modules
impact: HIGH
impactDescription: Module depth directly determines testability and maintainability
tags: design, modules, abstraction, ousterhout
---

# Deep Modules

From John Ousterhout's "A Philosophy of Software Design."

## Deep vs Shallow

A **deep module** has a small, simple interface but hides significant implementation complexity. A **shallow module** has a large or complex interface relative to the little work it does.

```
Deep module:             Shallow module:

+------------------+     +------------------------------------------+
|  small interface |     |          large interface                 |
+------------------+     +------------------------------------------+
|                  |     |                                          |
|                  |     +------------------------------------------+
|   lots of        |
|   implementation |
|                  |
|                  |
+------------------+
```

## Why This Matters for TDD

Deep modules are easier to test because:
- Small interface = fewer test cases to cover the API surface
- Complex internals are hidden = tests don't couple to implementation
- Refactoring internals does not break tests

Shallow modules are painful to test because:
- Many parameters and options to exercise
- Tests mirror the implementation rather than verifying behavior
- Every internal change breaks tests

## Examples

### Deep: `io.Reader` (Go)

```go
type Reader interface {
    Read(p []byte) (n int, err error)
}
```

One method. Hides whether the source is a file, network socket, compressed stream, or in-memory buffer. Trivial to test: pass bytes in, check bytes out.

### Shallow: config struct with 20 fields

```go
type ServerConfig struct {
    Host            string
    Port            int
    ReadTimeout     time.Duration
    WriteTimeout    time.Duration
    IdleTimeout     time.Duration
    MaxHeaderBytes  int
    TLSCertFile     string
    TLSKeyFile      string
    // ... 12 more fields
}
```

Every field is part of the interface. Tests must cover combinations. Refactoring any field breaks callers.

### Deep: `GenServer` with simple API (Elixir)

```elixir
defmodule RateLimiter do
  # Public API: 2 functions
  def allow?(key), do: GenServer.call(__MODULE__, {:check, key})
  def reset(key), do: GenServer.cast(__MODULE__, {:reset, key})

  # Internal: sliding window, token bucket, cleanup -- all hidden
end
```

Two-function interface. The entire rate-limiting algorithm is an implementation detail. Tests call `allow?/1` and `reset/1`.

## Design Heuristic

When designing a module, ask:

1. Can I describe the interface in one sentence?
2. Would a caller need to understand internals to use it correctly?
3. Could I swap the implementation without changing tests?

If the answer to (1) is no, the interface is too wide. If (2) is yes, the abstraction is leaking. If (3) is no, tests are coupled to implementation.

## Relationship to TDD

During Phase 1 (Planning), design deep modules. If the interface you sketch requires many tests just to cover parameter combinations, simplify the interface before writing any code.
