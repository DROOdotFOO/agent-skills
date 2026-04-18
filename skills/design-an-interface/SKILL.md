---
name: design-an-interface
description: |
  Design interfaces using Ousterhout's "Design It Twice" method with parallel sub-agents.
  TRIGGER when: user asks to design an API, interface, module boundary, or public surface area, or says "design it twice."
  DO NOT TRIGGER when: user already has a specific interface and wants implementation, or is refactoring internals without changing the public API.
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: design, interface, ousterhout, api, modules, parallel-agents
---

# Design an Interface

## Philosophy

Every interface design involves tradeoffs you cannot see from a single perspective. Designing it twice (or three times) with radically different constraints forces you to explore the design space before committing. This skill spawns parallel sub-agents, each constrained differently, then compares and synthesizes.

## Workflow: 5 Phases

### Phase 1: Gather Requirements

Before spawning any sub-agents, clarify:
- What problem does this interface solve?
- Who are the callers? What do they need?
- What are the invariants the interface must preserve?
- What are the performance / ergonomic / safety constraints?

Do NOT start designing until requirements are agreed upon.

### Phase 2: Spawn Divergent Sub-Agents

Launch 3+ parallel sub-agents (via `Agent` tool with `subagent_type`), each given the same requirements but a different constraint set. Constraints must force **radically different** designs -- not minor variations. See [constraints.md](constraints.md) for examples.

Each sub-agent produces:
- Interface definition (function signatures, types, module API)
- Usage example for the most common case
- One paragraph on the tradeoff it optimized for

### Phase 3: Present Designs

Show all designs side-by-side. Label each by its primary constraint. Do not editorialize yet -- let the user see the raw options.

### Phase 4: Comparative Evaluation

Evaluate every design against Ousterhout's criteria. See [evaluation-criteria.md](evaluation-criteria.md) for the full rubric. Score each design on:
- Depth (small interface, rich implementation)
- Simplicity of the common case
- Resistance to misuse
- General-purpose vs specialized tradeoff
- Implementation efficiency

### Phase 5: Synthesize

Combine the best elements into a final design. Explain which parts came from which design and why. The synthesis is often none of the originals -- it is a new design informed by all of them.

## Rules

- Never present fewer than 3 designs.
- Designs must be structurally different, not cosmetic variations.
- Evaluate on caller ergonomics, not implementation convenience.
- Prefer deep modules: small interface surface, rich behavior behind it.
- If all designs converge, your constraints were too similar -- re-run with harder constraints.

## What You Get

- Three or more structurally distinct interface designs, each optimized for a different constraint set.
- A side-by-side comparative evaluation scored against Ousterhout's criteria (depth, simplicity, misuse resistance).
- A synthesized final design that combines the strongest elements from all candidates, with rationale for each choice.

## Sub-files

| File | Topic |
|------|-------|
| [evaluation-criteria.md](evaluation-criteria.md) | Ousterhout evaluation rubric |
| [constraints.md](constraints.md) | Divergent constraint sets for sub-agents |
