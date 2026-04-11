---
title: Full procedure (Steps 0-8)
impact: CRITICAL
impactDescription: The complete step-by-step workflow including three-tier roster building, persona composition, quality checks, and parallel agent spawning
tags: procedure, workflow, roster, personas, spawning
---

# Procedure

## Step 0 [MANDATORY] -- Triage (the go/no-go gate)

Answer all 4 questions in writing before doing anything else:

1. What is the one-sentence problem? (If you can't write it, ask the user.)
2. What's the user's success criterion? (If you can't state it, ask.)
3. What cheaper method was tried first (single Agent, direct reasoning, paper search), and why was it insufficient?
4. Does the problem have at least one **concrete noun** (system, dataset, domain) AND at least one **concrete constraint or known failure**?

If question 4 is no, the input is too vague -- STOP and ask the user one clarifying question. Do not enter Step 1 with a content-free problem. The smallest dangerous input is "I'm stuck on this, what am I missing?" -- 10 words, hits two trigger phrases, produces 12 confabulated hypotheses about a problem nobody stated.

## Step 1 -- Frame the problem as math objects (LOOSE)

Strip surface vocabulary. Write a structural feature list as a **visible markdown bullet list**. This is used for two things only: (a) the "somewhat relevant" gate in Step 2, and (b) post-hoc testing of returned hypotheses in Step 9. **It is NOT the generator of lens candidates**.

Starter prompts (NOT exhaustive):

**Quantitative-structural features:**
- Discrete states with transitions?
- Probability distributions over a small alphabet?
- Cross-thing comparison with partial data?
- Network with conserved topology, varying weights?
- Hierarchical levels coupled together?
- Trajectories through state space under constraints?
- Rare events / small samples?
- Mutual exclusivity / one-hot constraints?
- Adversarial / co-evolutionary dynamics?
- Algebraic operations on objects?

**Non-quantitative structural features:**
- Self-reference / quine structure / system describes itself?
- Performative / speech-act / saying-as-doing?
- Normative / deontic / "ought" rather than "is"?
- Narrative / sequence-of-irreversible-commitments?
- Aesthetic / taste-judgment / coherence rather than truth?
- Strategic / signal under common knowledge / bluff possible?

Add at least one feature **in your own words** that isn't in either list. If you cannot, you haven't finished framing.

**Abort condition**: if your decomposition produces fewer than 3 features, the problem may not be polymath-shaped. Consider whether single-Agent direct work is more appropriate.

## Step 2 [MANDATORY] -- Build three tier rosters by PARALLEL max-distance walks

**Build the three rosters as a separate task from understanding the problem.** Do NOT consult Step 1's structural features during this step except as a loose relevance gate.

Each final agent in Step 8 will be a polymath expert carrying three domain traits -- one from each tier. See [core-insight.md](core-insight.md) for tier band definitions.

**Procedure -- spawn three roster-builder sub-agents IN PARALLEL** (single message, multiple tool-use blocks). Each gets the _same_ one-line problem statement and _only_ their tier assignment. They MUST NOT see each other's output. They MUST NOT see Step 1's structural feature list. Parallel dispatch is load-bearing: sequential dispatch lets the orchestrator leak intuitions from the first returned roster into how it briefs the next, collapsing tier diversity.

Each roster-builder runs the same algorithm within its tier:

```
roster_tier = []
seed = pick any domain inside {this tier's relatedness band}
roster_tier.append(seed)

while True:
    candidate = the field that is BOTH:
       (i)  inside this tier's relatedness band to the substrate, AND
       (ii) maximally far from EVERY domain already in roster_tier

    if no candidate satisfies both constraints:
        STOP -- this tier's roster is complete

    roster_tier.append(candidate)

    if len(roster_tier) >= N:  # orchestrator specifies N per tier, default 12
        STOP
```

**Target size per tier**: N = 12 (orchestrator may override in [8, 15]). All three tiers should aim for the same N.

**The relevance gate is intentionally weak**, especially for T_far. If a roster-builder is rejecting candidates because "I don't see how X applies", it is applying the wrong filter -- that question is for Step 9, not Step 2.

**Lower bound**: N = 8 per tier (24 total candidates). Below this, sampling in Step 2b can't produce enough non-redundant polymath composites.

**Per-project roster cache (T_close and T_mid only)**: T_close and T_mid are substrate-stable across rounds. Cache them after the first round.

- **Cache path**: `results/polymath/rosters-cache/{substrate-slug}.json`
- **Schema**: `{"substrate": "...", "built_at": "YYYY-MM-DD", "t_close": [...], "t_mid": [...], "notes": "..."}`
- **On a new round**: check the cache first. If present, load T_close and T_mid from disk and only spawn ONE roster-builder (for T_far). Announce the reuse to the user.
- **Do NOT cache T_far.** T_far is where wildness lives. Always re-spawn.
- **Cache invalidation**: (a) substrate description materially changes, (b) project journal records substrate-redefinition, (c) >90 days passed, (d) user explicitly requests `--fresh-rosters`.
- **Full re-shuffle on every new iteration** (MANDATORY when reusing cache): Step 2b MUST re-draw the 3-way matching, re-sample the prime per persona, and re-write fresh mini-stories. Never carry personas over from a previous round.

## Step 2b [MANDATORY] -- Compose polymath expert personas

After all three rosters return, compose the N polymath personas in the orchestrator (NOT in a sub-agent -- only the orchestrator has all three rosters simultaneously).

**Composition rule -- one trait per tier, plus a randomly-chosen PRIME, plus an expert role, plus a one-sentence mini-story.** For each of the N personas:

1. **Sample one domain from T_close** -- call it `d_close`.
2. **Sample one domain from T_mid** -- call it `d_mid`.
3. **Sample one domain from T_far** -- call it `d_far`.
4. **Choose the PRIME at random** from `{d_close, d_mid, d_far}`. The prime is the persona's _current primary work_ -- the field they spend their day in. The other two become background/prior career/hobby.
    - **T_close-too-niche escape hatch**: if `d_close` is too narrow to be someone's day job as a standalone expert, exclude it from the prime lottery and pick prime from `{d_mid, d_far}`.
    - Why random prime matters: if prime is always T_close, every persona anchors its self-identity to the substrate's neighborhood and the tiers' spread gets flattened at the identity layer.
5. **Assign an expert role** that fits the chosen PRIME: researcher, engineer, consultant, practitioner, clinician, designer, analyst, craftsman, curator, translator, coach, or any role whose work requires **thoughtful, non-routine judgment**. Roles like "data entry clerk", "cashier" are NOT eligible.
6. **Write a one-sentence mini-story** explaining why this combination of three domains ended up in one human. Reference at least two domains and gesture at a specific life moment or motivation. The story lets the persona reason from a felt identity instead of a template.

**Sampling discipline:**
- Use each domain **at most once across the N personas** unless N exceeds roster size. Sampling with replacement defeats the spread.
- Randomize the 3-way matching (don't pair index 0 of each tier together).
- Randomize the prime per-persona independently.
- Across all N personas, the prime distribution should NOT be all T_close. If after N draws the prime is never T_mid or never T_far, re-roll until all three tiers are represented as primes at least once (when N >= 6).
- Write the full N personas as a visible markdown block before Step 7. Each entry:
    - Line 1: `Persona #k: {expert role} in {PRIME domain}; background in {other two domains}`
    - Line 2: `Story: {one-sentence mini-story}`

**Reference example** (substrate = feline histiocytic sarcoma mutation prediction):
> **Persona #3**: research engineer in historical corpus linguistics; background in bioinformatics genome-assembly pipelines and software systems engineering.
> **Story**: Started her career writing distributed-systems code at a search-infra company, burned out and did a CS-for-biologists bootcamp that landed her on a sequencing-pipeline team for five years, then discovered historical linguistics via a reading group on comparative Indo-European morphology and now runs a lab that treats medieval manuscripts as noisy biological sequences -- because to her they obviously are.

**Target N**: 8-12 personas. Minimum 4. Maximum 15.

## Step 3 -- Identify substrate (implicit, single)

The "substrate" is the user's actual problem domain -- typically obvious and singular. It is NOT a separate axis to be paired against personas. Each agent in Step 8 approaches the substrate from their layered polymath perspective. The substrate is constant; only the persona varies.

## Step 4 [MANDATORY] -- Walk the abstraction ladder (post-roster check)

After Step 2 produces the three tier rosters AND Step 2b composes the personas, walk the abstraction ladder and check coverage on the union pool (T_close U T_mid U T_far).

If the problem has natural ordering axes -- physical scale, temporal scale, OR **representational scale** (syntax -> semantics -> pragmatics -> meta) -- list them and confirm the combined domain pool includes at least one domain at each level the problem touches.

For each scale, write **one sentence** explaining what a domain at that scale would SEE that domains at other scales would miss. If a scale is uncovered, **return to Step 2 and re-spawn the tier whose band most naturally covers that scale**. Re-sample the affected personas in Step 2b.

If you cannot find a domain that satisfies the constraint, mark the scale as an OPEN FEATURE in the synthesis doc.

## Step 5 -- "What scares it" pass (post-roster check)

What failure modes does this problem have? For each, check whether the combined domain pool has a domain that specializes in defeating it:

- Tiny n -> Bayesian shrinkage, hierarchical models (likely T_close or T_mid)
- Train/deploy drift -> domain adaptation, covariate shift (T_close or T_mid)
- Multimodality -> MCMC mixing, optimization (T_mid)
- Asymmetric missing data -> survey statistics, missing-data theory (T_mid)
- Confounding -> causal inference, propensity scoring (T_close or T_mid)
- Reproducibility cliff -> meta-science, calibration theory (T_mid or T_far)
- Adversarial selection -> cryptography, game theory (T_mid or T_far)

If a critical failure mode has no domain in the pool, return to Step 2 for one more iteration of the tier most naturally holding that methodology.

## Step 6 [MANDATORY] -- T_far sanity check (non-STEM coverage)

Count how many domains in **T_far** come from fields with no STEM overlap (art, law, linguistics, trades, humanities, religious studies, sport, sedimentology, forensics, music theory, architecture, crafts, games, cooking, OR/queueing, sports coaching).

If fewer than **ceil(N/2)** non-STEM entries are present in T_far, the T_far walk collapsed into a quant-STEM cluster and the far tier is doing the middle tier's job. **Re-spawn the T_far builder with an explicit non-STEM seed**.

(T_close and T_mid are allowed to be fully STEM -- their job is leverage, not wildness.)

## Step 7 [MANDATORY] -- Pre-spawn checklist (READ-DO)

Before composing the sub-agent calls, fill out this checklist visibly. Announce it to the user. Do not spawn until every box is checked AND the user has had a chance to refuse.

```
PRE-SPAWN CHECKLIST
[ ] N personas in [4, 15]: ___
[ ] Three tier rosters built by PARALLEL sub-agents in ONE message (K2)
[ ] Each tier's roster was generated by max-distance walk within its relatedness band, NOT by feature-matching
[ ] T_close, T_mid, T_far bands are visibly distinct (no T_mid member could pass as T_close or T_far)
[ ] T_far contains >= ceil(N/2) non-STEM domains (Step 6)
[ ] At least 3 abstraction-ladder levels covered by the union pool (Step 4)
[ ] Critical failure modes have at least one defending domain in the pool (Step 5)
[ ] N personas composed, each = expert role + one T_close + one T_mid + one T_far (Step 2b)
[ ] Each persona has a randomly-chosen PRIME (current-work domain) from among its three sampled domains
[ ] Prime distribution across the N personas is NOT all T_close -- T_mid and T_far each appear as prime at least once when N >= 6
[ ] T_close-too-niche escape hatch applied where needed
[ ] Each persona's expert role fits its PRIME and requires non-routine judgment
[ ] Each persona has a one-sentence mini-story referencing >= 2 domains and a specific life moment
[ ] Sampling was without replacement across personas (each tier domain used at most once)
[ ] Persona list shown to user as visible markdown block before any Step 8 spawn
[ ] Roster cache checked: T_close/T_mid loaded from cache if present and valid, OR freshly built
[ ] T_far was freshly spawned this round (never cached)
[ ] Personas were re-shuffled from scratch this round (fresh 3-way matching, fresh prime draws, fresh mini-stories)
[ ] Each brief has CONTEXT block with all 5 sub-slots filled (K5)
[ ] All Step 8 sub-agent blocks will be in ONE message (parallel) (K4)
[ ] Format string is verbatim from the template below
[ ] Cost announced: "Spawning 3 roster-builders, then N=__ polymath agents in parallel, ~M minutes wall time total."
[ ] User explicitly invoked the skill OR I have asked and received confirmation
[ ] Idempotency check: no prior polymath round exists for this problem (or user specified extend/replace)
```

## Step 8 [MANDATORY] -- Spawn N parallel polymath-persona sub-agents

Use whatever sub-agent tool is available in your current environment (historically named `Agent` or `Task`). If only sequential spawning is available, state this limitation to the user and ask whether to proceed serially or abort.

**Launch all agents in a single message** with multiple tool-use blocks. Sequential dispatch is the [K4] silent failure.

Each agent gets a **self-contained brief** (it has zero context from this conversation). Each agent embodies ONE composed polymath persona from Step 2b and examines the substrate from that layered perspective.

```
You are a {EXPERT_ROLE} in {PRIME_DOMAIN}. Your background includes {OTHER_DOMAIN_A} (from an earlier part of your career or training) and {OTHER_DOMAIN_B} (a lifelong serious interest). You are the kind of practitioner whose work requires thoughtful, non-routine judgment -- not a procedural executor.

Your personal story, in one sentence -- inhabit this, do not just reference it:
{PERSONA_MINI_STORY}

You are approaching a problem from outside the substrate community's usual framing. Your value is NOT that you know one field well -- many people do. Your value is that you carry three domains in one head and can recognize when they are secretly talking about the same object.

{ONE-LINE PROBLEM STATEMENT}

CONTEXT (self-contained -- assume no prior knowledge):
- PROBLEM NUMBERS: {specific data points with units}
- PRIOR FINDINGS: {quote exact text or cite source}
- WHAT'S BEEN TRIED: {prior attempts and why insufficient}
- CONSTRAINTS: {what cannot be assumed/done}
- DEAD ENDS / NOT TO PROPOSE: {known failures}
- SUCCESS CRITERION: {what makes a hypothesis useful here}

YOUR PRIMARY TASK IS ISOMORPHISM HUNTING. You are specifically looking for cases where an object, operation, or failure mode in the substrate problem is *structurally the same* as something you already know in {PRIME_DOMAIN}, {OTHER_DOMAIN_A}, or {OTHER_DOMAIN_B} -- even if the vocabularies look nothing alike. The highest-value output is "these two things are actually the same object; here is the mapping; here is a theorem/method my side already uses for it".

Propose 2-3 specific items, ranked from most to least valuable:

1. **Multi-domain isomorphism items** (highest value): identify a concept, object, or method that is native to TWO OR MORE of your three domains simultaneously, and explain how it maps onto the substrate. "In {PRIME} we call this X, in {OTHER} we call it Y, and I think your problem is a third instance of the same structure because..." These are the rarest and most useful items.

2. **Single-domain transplant items** (also valid): "in {one of your domains} we usually do X for this kind of situation -- maybe it will help you?" Lower-value than isomorphisms but still useful.

3. For EACH item: tag which of your three domains it draws from. Use [prime], [bg-A], [bg-B], or combinations like [prime+bg-B], [bg-A+bg-B], or [all-three].

4. Re-describe the problem in at least one of your domain's native vocabularies before answering -- this is how you catch isomorphisms you would otherwise miss.

5. If a structural correspondence looks crazy at first but becomes defensible on reflection, SAY IT. Wild-but-wrong is cheap to discard; wild-but-right is the entire point.

If the context is insufficient to ground a response, return `INSUFFICIENT CONTEXT: <what's missing>` instead of guessing. Do not fill gaps with plausible confabulation.

Format: Return ONLY the items, numbered, with a one-line title each. Prefix each item with the domain tag ([prime], [bg-A], [bg-B], [prime+bg-A], etc.). No preamble. Each item 3-5 sentences with a clear testable claim OR a clear structural mapping. For structural/re-framing domains (category theory, linguistics, philosophy of science, music theory, ritual studies), substitute "testable prediction" with "re-description of the problem in your domain's native vocabulary, plus the specific isomorphism or method that re-description exposes".
```

**Hard rules for the brief:**
- If any of the 5 CONTEXT sub-slots is empty, justify why in a comment OR rewrite. Empty sub-slots produce confabulation.
- Total context block <=3KB per brief -- pre-summarize substrate data into a shared block reused verbatim across all agents; only the persona identity varies.
- **PII / clinical data**: before inlining clinical, patient, or identifying data, check whether it's safe to replicate N times. Prefer handles or citations over full records unless the user explicitly confirms.
- The {ONE-LINE PROBLEM STATEMENT} and CONTEXT block should be **identical** across all N briefs.
