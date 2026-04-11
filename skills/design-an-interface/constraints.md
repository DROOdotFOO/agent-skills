---
title: Constraint Sets for Sub-Agents
impact: HIGH
impactDescription: Similar constraints produce similar designs, defeating the purpose of designing it twice
tags: design, constraints, divergence, sub-agents, parallel
---

# Constraint Sets for Sub-Agents

The goal is **radical divergence**. If two designs look similar, the constraints were too weak. Each sub-agent receives the same requirements but a different constraint that forces a fundamentally different interface shape.

## Example Constraint Sets

### Minimize Method Count

"Design an interface with the absolute minimum number of public methods. Combine operations where possible. Prefer configuration objects over method variants. Target 3 methods or fewer."

Forces: deep modules, configuration-driven APIs, convention over enumeration.

### Maximize Flexibility

"Design an interface that handles every foreseeable extension without modification. Prefer composition, callbacks, middleware patterns. No method should assume a specific use case."

Forces: plugin architectures, higher-order functions, protocol/trait-based design.

### Optimize for the Common Case

"Design an interface where the single most common operation is a one-liner with zero configuration. Sacrifice generality for ergonomics. Power users can drop to a lower-level API."

Forces: progressive disclosure, layered APIs, sensible defaults.

### Borrow from a Specific Paradigm

"Design this interface as if you were writing idiomatic [Haskell / Smalltalk / Unix CLI / REST / SQL]. Adopt that paradigm's conventions even if they feel unusual here."

Forces: completely different mental model, often reveals hidden assumptions.

### Immutable by Default

"Design an interface where all operations return new values. No mutation, no side effects in the core API. Side effects are pushed to the boundary."

Forces: functional core, separation of pure logic from effects.

### Single Struct / Single Function

"Expose exactly one type and one function. All behavior is controlled by the shape of the input and output types."

Forces: data-oriented design, parse-don't-validate, algebraic data types.

## How to Ensure Radical Difference

1. Pick constraints from different rows above -- never two that are philosophically adjacent.
2. If you have a "minimize" constraint, pair it with a "maximize" constraint.
3. Include at least one constraint from a paradigm the team does not normally use.
4. After designs are produced, check: could you tell them apart from the type signatures alone? If not, re-run.

## Anti-Patterns

**Similar designs**: all three designs have the same method names with slightly different signatures. This means the constraints were too weak or the sub-agents interpreted them loosely. Fix: make constraints more extreme.

**Skipping comparison**: jumping to "I like design B" without scoring all designs against the evaluation criteria. The point is systematic comparison, not gut feel.

**Evaluating by implementation effort**: "Design A is easier to implement" is not a valid reason to prefer it. Interfaces are for callers, not implementers. Implementation effort is a one-time cost; caller friction is permanent.

**Premature convergence**: synthesizing before the user has seen and discussed all designs. Present first, evaluate second, synthesize third.
