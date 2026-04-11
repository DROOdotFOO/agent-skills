---
title: Anti-patterns, error states, variants, and extensions
impact: HIGH
impactDescription: Comprehensive catalog of failure modes, recovery procedures, workflow variants, self-application rules, and domain-specific extension points
tags: anti-patterns, error-handling, variants, extensions, meta
---

# Reference

## Error states and fallbacks

| Failure | Action |
|---|---|
| Harness forbids parallel sub-agents | State limitation, ask whether to serialize or abort |
| Sub-agent tool renamed/missing | Use whatever the current sub-agent tool is named; if none exists, abort and tell the user |
| User interrupts mid-spawn | If <60% returned: do not synthesize, ask whether to resume; if >=60%: synthesize partial, flag uncovered scales/lenses explicitly |
| Agent returns prose instead of format | Re-spawn that one lens with stricter brief; do not synthesize malformed returns |
| 3+ agents return INSUFFICIENT CONTEXT | The CONTEXT block was [K5] failure -- fix it and re-spawn the failures |
| All agents converge on same hypothesis | Could be robustness OR roster collapse. Run robustness check in synthesis template; if assumptions overlap, run a second round with a non-STEM seed |
| Max-distance walk gets stuck | This IS the natural stopping rule -- do not force it. A roster of 6 honestly-distant lenses beats 12 with 6 forced |
| Max-distance walk produces only STEM lenses | Step 6 failure -- restart with a non-STEM seed (humanities, art, religious studies, trades) |
| User re-invokes on same problem | Check for prior `results/polymath/*` artifacts. If found: ask whether to extend, replace, or critique existing -- do NOT silently re-spawn |

## Anti-patterns

- **Substrate-anchored roster generation**: walking your structural-feature list and asking "what field has this object?" -> produces feature-matched lenses biased toward what you already see. Use parallel tier walks instead.
- **Sequential tier construction**: building T_close first, then T_mid, then T_far -> the orchestrator leaks intuitions from earlier tiers into how it briefs later ones. Always spawn the three roster-builders in parallel.
- **Role is a procedural worker**: composing a persona whose expert role is "data entry clerk", "cashier", or any role without judgment under uncertainty -> defeats the thoughtful-decision constraint.
- **Single-tier persona**: giving an agent only one domain instead of sampling one-per-tier -> stops being a polymath and becomes a plain lens agent.
- **Same-index pairing**: pairing `T_close[0]` with `T_mid[0]` with `T_far[0]` -> the roster-builders' internal ordering biases the composites. Randomize the 3-way matching.
- **T_far collapsed into STEM**: T_far contains mostly quant fields -> the far tier is doing the middle tier's job. Re-spawn with a non-STEM seed.
- **Tier bleed**: a "T_mid" domain that would actually pass as T_close (or vice versa) -> the relatedness bands weren't enforced.
- **Sampling with replacement when unneeded**: using the same domain across multiple personas when the tier is large enough -> defeats spread.
- **Carrying personas across rounds**: caching the persona table itself instead of just the rosters -> pins the matching and prime distribution to a single roll.
- **Always-T_close prime**: composing every persona with its PRIME set to T_close -> collapses the breadth-first advantage of random-prime.
- **Missing mini-story**: composing personas as bare tuples without the one-sentence backstory -> the agent defaults to a template response instead of reasoning from a felt identity.
- **Roster-from-memory**: pulling 12 famous fields without doing the walks -> tiers cluster around the user's training distribution.
- **Scale clustering**: every domain in the union pool lives at the same abstraction level -> run Step 4 explicitly.
- **Loose output format**: agents return prose essays -> always specify format string verbatim, including the domain tags.
- **Sequential Step 8 dispatch**: persona agents fire one at a time -> [K4] failure.
- **Premature averaging in synthesis** -> defeats the entire point.
- **Cargo-culting a prior round's rosters** -> defeats the parallel tier walks entirely.
- **Confabulation from thin context**: empty CONTEXT sub-slots -> agents fluently invent.
- **Triggering on debugging**: "I'm stuck on this regex" -> false positive, burns budget.
- **Using the structural decomposition as a generator**: decomposition is for the relevance gate and post-hoc tests only.

## Variants

Same workflow, different framing-question template:

- **Hypothesis generation** (default): "What might be true?"
- **Failure-mode audit**: "What could break? What are we missing?"
- **Data/normalization audit**: "What relationships, scaling, or confounders might we be passing wrong?"
- **Architecture critique**: "What's structurally weak about this design?"
- **Naming/framing search**: "What's a better vocabulary for this problem?"

Map user verbs to variants: "hypotheses/ideas" -> generation; "what could break / poke holes" -> failure-mode audit; "review/critique/challenge" -> architecture critique. Swap framing questions in Step 8; keep the rest of the methodology identical.

## Self-application (meta-use)

This skill CAN be applied to itself, but only as a **failure-mode audit variant** -- never as hypothesis generation. The recursion is sound for one level; beyond that, the lens roster necessarily degenerates because all meta-lenses share the substrate "documentation that programs a future executor".

**Meta-application rule**: when the substrate is a methodology document, run the max-distance walk with seeds from fields that study _artifacts-describing-themselves_: metalogic, type theory, legal self-amendment, ritual studies, IFS, quine theory, constitutional drafting, pedagogy of unteachable skills, aviation checklist science, API design.

**Convergence-vs-collapse rule**: when >=70% of meta-lenses converge on the same finding, you cannot tell from inside the round whether it's a robustness signal or a roster-collapse artifact. The disambiguator is a second walk starting from a maximally distant seed; if your budget doesn't allow that, mark the finding as "convergent under {your roster's seed}" rather than "robust".

**Sub-agents cannot themselves invoke this skill.** No grandchild spawning. If recursion is needed, return to the root orchestrator and run a second round.

### Blindspots of this skill (Godel clause)

The polymath workflow structurally CANNOT see:

- When the problem is mis-stated at the substrate level (Step 1 trusts the user's framing)
- When the user's goal is emotional/relational, not epistemic
- When spawning more agents is procrastination
- When the substrate vocabulary itself is the trap
- When convergence reflects the model's training distribution, not the real possibility space

If your problem lives in one of these blindspots, no number of lenses will help. Stop and reframe manually.

## Domain-specific extensions

Substrate-specific rosters and known failure modes live in extension skills (in project-local `.claude/skills/` directories):

- `polymath-bio` -- biology / biomedical research

Note: extension skills now provide **example seeds** and **failure-mode catalogs**, NOT lens menus. The max-distance walk is always the canonical roster generator. Lens lists in extensions are memory aids for what's been productive in past rounds -- never substitutes for running the walk.
