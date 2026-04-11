---
title: Quality gate and synthesis template
impact: CRITICAL
impactDescription: Step 9a quality gate prevents confabulated/malformed briefs from polluting synthesis. Step 9 template enforces structured output that preserves disagreement instead of averaging
tags: synthesis, quality-gate, template, output
---

# Quality Gate and Synthesis

## Step 9a -- Quality gate (triage returned briefs)

Before synthesis, check each returned brief:

- Matches the format (numbered items, each prefixed with [prime]/[bg-A]/[bg-B]/combination tag)?
- >=2 items returned?
- Names specific methods, not vague gestures?
- At least one item draws on T_mid or T_far (if all items are [prime]-tagged and the prime is T_close, the persona collapsed into a single-domain agent and its T_mid/T_far traits did no work)?
- Returned `INSUFFICIENT CONTEXT`? -> the persona is unusable, do NOT include in synthesis
- Pair-wise: any two briefs with >80% lexical overlap? -> flag as correlation failure (the tier walks failed to actually distance the personas)

If <60% of agents produced usable output, do NOT synthesize. Report the failure to the user, name which abstraction levels / failure modes / T_far non-STEM domains ended up uncovered, and ask whether to re-spawn the failed personas (and whether to re-sample from the existing rosters or re-run the parallel tier walks).

## Step 9 [MANDATORY] -- Synthesize into a landscape doc

Use this template verbatim. Free-prose synthesis is [K6] failure -- averaging happens by accident.

```markdown
# {Problem slug} -- polymath landscape, {YYYY-MM-DD}

## Tier rosters
| Tier | Members |
|------|---------|
| T_close | {comma-separated list in the order the T_close builder added them} |
| T_mid   | {comma-separated list in the order the T_mid builder added them} |
| T_far   | {comma-separated list in the order the T_far builder added them} |

## Personas
| # | Expert role | PRIME domain (tier) | Background domains | Mini-story | Status |
|---|-------------|---------------------|---------------------|------------|--------|
{one row per composed persona; PRIME tier = close/mid/far}

## Convergent hypotheses (>=3 personas reached independently)
{For each: name + which personas + the mechanism each cited + the dominant domain tag ([prime] / [bg-A] / [bg-B] / [multi]).
ROBUSTNESS CHECK: list each converging persona's PRIME tier and its domain assumptions. If convergence is carried only by personas whose PRIME is T_close, it may be a substrate artifact, not robustness -- flag as such.}

## Isomorphism hits (multi-domain tagged items)
{List every item any persona tagged with a combination tag ([prime+bg-A], [all-three], etc.). These are the highest-value outputs of the round -- concrete evidence that composing polymath personas from three tiers paid off. For each: which persona, which two/three domains, the named shared object, and the method/theorem the persona claims transfers.}

## Unique-persona hypotheses (exactly 1 persona reached)
{For each: name + which persona + which of its three domains carried the idea + why the other personas missed it.
Unique hypotheses from T_far-PRIMED personas are especially high-value -- they are what the random-prime rule exists to produce.}

## Active disagreements
{For each pair of contradictory hypotheses: state both, predict what experiment would discriminate them. Do NOT resolve.}

## Open features
{Structural features from Step 1 that no lens addressed, OR abstraction-ladder scales the roster failed to cover -- the genuinely-novel territory.}

## Unreached regions
{Failure modes / non-STEM domains your roster did NOT cover. Marks where a follow-up round should aim.}

## Testability tiers
- (a) testable from existing data immediately: ...
- (b) testable from data we could plausibly get: ...
- (c) requires new experiments: ...
- (d) currently untestable: ...

## What would change my mind about the convergence pattern
{If convergent hypotheses share assumptions, what orthogonal-roster round would disambiguate? Specifically: what non-STEM seed should the next walk start from?}
```

## Termination

The workflow ends when the landscape doc is written to a file (suggested path: `results/polymath/YYYY-MM-DD-{problem-slug}/landscape.md`) AND presented to the user with the question:

> **"Which region of this map do you want to explore first?"**

Do not pick for the user. Do not start implementing a hypothesis without their selection. The skill produces a map, not a recommendation.
