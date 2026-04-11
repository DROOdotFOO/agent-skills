---
name: polymath
description: >
  Polymath split-brain research methodology. Maps the possibility space of
  open-ended problems by building a max-distance lens roster across three
  relatedness tiers (close/mid/far), composing polymath expert personas from
  the tiers, spawning N parallel sub-agents, then synthesizing their
  disagreements into a landscape map.
  TRIGGER when: the user explicitly invokes the technique
  ("polymath", "split-brain", "multiagency", "let's run agents to/for X",
  "remember our polymath multiagency"), OR when ALL of these are true:
  (a) the problem is research/strategy/framing-level, (b) the user has
  indicated framing uncertainty (not debugging), (c) the cost of picking the
  wrong frame is high, (d) the user has not already specified an approach.
  DO NOT TRIGGER when: debugging ("stuck on this regex/error/build/typo/merge
  conflict"), file/syntax lookups, single-answer questions, naming/styling
  micro-decisions, or anything where one direct answer would suffice. When the
  trigger match is ambiguous, ASK the user "split-brain this with ~10 polymath
  lenses, or just one targeted Agent?" -- one clarifying question is cheaper
  than 12 wasted spawns OR a missed framing discovery.
metadata:
  author: DROOdotFOO
  version: "2.0.0"
  tags: research, multi-agent, brainstorming, strategy, methodology
---

# Polymath Split-Brain Workflow

A meta-method for mapping the possibility space of a problem before committing to an approach. Forces uncorrelated views by spawning parallel agents that each see the problem through a different disciplinary lens. The value comes from the **spread** of returned ideas, not from averaging them -- disagreement is the signal.

## Killer items -- silent failures if skipped

These are load-bearing. Skipping any produces output that _looks_ successful but is wrong:

- **[K1] Step 0 triage produced an explicit go-decision** -- without this, the workflow burns lenses on a problem that didn't need them.
- **[K2] Step 2 rosters were built by THREE PARALLEL sub-agents (close/mid/far tiers), each running max-distance walk within its tier WITHOUT looking at the problem's specific features** -- without this, orchestrator bias leaks into tier construction and the composed polymath personas lose their spread.
- **[K3] Step 7 pre-spawn checklist was filled out and announced to the user before any sub-agent call** -- without this, the user has no chance to correct the framing or refuse the cost.
- **[K4] All sub-agent dispatches went out in a SINGLE message with multiple tool blocks** -- sequential dispatch silently wastes 10x wall-time.
- **[K5] Each agent's brief contains a self-contained CONTEXT block with all 5 required sub-slots filled** -- without this, agents confabulate from thin air.
- **[K6] Synthesis followed the mandatory output template (Step 9), not free prose** -- without this, "do not average" gets violated by accident.

## When this is the right tool

Use ONLY when ALL hold: the problem is research/strategy/framing-level; the "right" frame is genuinely unknown; the cost of picking the wrong frame is high; a single deep Agent call would not suffice (value is in _spread_, not depth on one axis).

DO NOT use when: the problem is well-defined; the user needs a specific factual answer; the user is debugging a specific error/build/syntax; the user wants K<5 ideas (use a single Agent); the output would fit in one paragraph; the harness forbids parallel sub-agent spawning.

## The core insight

Adjacent domains share assumptions with the substrate. You need lenses whose **objects look the same as yours but whose intuitions are different** -- isomorphism, not analogy. The generative move is **parallel max-distance walks at three relatedness tiers** (close/mid/far), then composing each agent as a polymath expert carrying one domain from each tier.

See [core-insight.md](core-insight.md) for the full explanation of three-tier stratification and the isomorphism test.

## Reading guide

| Task | Read |
|------|------|
| Full procedure (Steps 0-8) | [procedure.md](procedure.md) |
| Three-tier system, isomorphism vs analogy | [core-insight.md](core-insight.md) |
| Quality gate + synthesis template | [synthesis.md](synthesis.md) |
| Anti-patterns, error states, variants, extensions | [reference.md](reference.md) |
