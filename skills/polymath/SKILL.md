---
name: polymath
description: >
  Polymath split-brain research methodology. Maps the possibility space of
  open-ended problems by spawning N parallel sub-agents through maximally
  diverse disciplinary lenses, then synthesizing their disagreements into a
  landscape map. TRIGGER when: the user explicitly invokes the technique
  ("polymath", "split-brain", "multiagency", "let's run agents to/for X",
  "remember our polymath multiagency"), OR when ALL of these are true:
  (a) the problem is research/strategy/framing-level, (b) the user has
  indicated framing uncertainty (not debugging), (c) the cost of picking the
  wrong frame is high, (d) the user has not already specified an approach.
  DO NOT TRIGGER when: debugging ("stuck on this regex/error/build/typo/merge
  conflict"), file/syntax lookups, single-answer questions, naming/styling
  micro-decisions, or anything where one direct answer would suffice. When the
  trigger match is ambiguous, ASK the user.
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: research, multi-agent, brainstorming, strategy, methodology
---

# Polymath Split-Brain Workflow

A meta-method for mapping the possibility space of a problem before committing to an approach. Forces uncorrelated views by spawning parallel agents that each see the problem through a different disciplinary lens. The value comes from the **spread** of returned ideas, not from averaging them — disagreement is the signal.

## Killer items — silent failures if skipped

These are load-bearing. Skipping any of them produces output that _looks_ successful but is wrong. Mark each one as done before claiming the workflow ran:

- **[K1] Step 0 triage was performed and produced an explicit go-decision** — without this, the workflow burns lenses on a problem that didn't need them.
- **[K2] Step 2 roster was built by max-distance walk WITHOUT looking at the problem's specific features** — without this, substrate bias collapses lens diversity and the roster recapitulates the substrate's vocabulary.
- **[K3] Step 7 pre-spawn checklist was filled out and announced to the user before any sub-agent call** — without this, the user has no chance to correct the framing or refuse the cost.
- **[K4] All sub-agent dispatches went out in a SINGLE message with multiple tool blocks** — sequential dispatch silently wastes 10x wall-time and still returns results, so this failure is invisible.
- **[K5] Each agent's brief contains a self-contained CONTEXT block with all 5 required sub-slots filled** — without this, agents confabulate from thin air and return polished but ungrounded hypotheses.
- **[K6] Synthesis followed the mandatory output template (Step 9), not free prose** — without this, "do not average" gets violated by accident and the spread collapses.

## When this is the right tool

Use ONLY when ALL of these hold:

- The problem is research/strategy/framing-level, not execution/debugging/lookup
- The "right" frame is genuinely unknown — multiple plausible framings exist
- The cost of picking the wrong frame is high relative to the cost of running 10+ agents
- A single deep Agent call would not suffice (the value is in _spread_, not depth on one axis)

DO NOT use when:

- The problem is well-defined and the solution method is known -> direct work
- The user needs a specific factual answer -> Read/Grep/single Agent
- The substrate domain is the bottleneck -> read more papers, don't spawn lenses
- The user is debugging a specific error, file path, syntax, build, or named bug -> not framing problems
- The user is asking for K<5 ideas -> use a single Agent with K internal lenses instead
- The output would fit in one paragraph
- The harness forbids parallel sub-agent spawning AND no fallback is acceptable

## The core insight

Brainstorming domains gives you what's _culturally adjacent_ to the problem — exactly the wrong move, because adjacent domains share assumptions with the substrate. You need lenses whose **objects look the same as yours but whose intuitions are different**. That's isomorphism, not analogy.

But the _generative_ move that produces good lenses is NOT "look at my problem and find isomorphic fields". That anchors lens selection to the substrate's vocabulary — the very bias the workflow exists to escape. The right generative move is **greedy max-distance walk**:

> Pick any loosely-relevant domain. Then iteratively add the field that is (a) somewhat relevant to the problem AND (b) as far as possible from every domain already in the roster. Build the roster as a SEPARATE TASK from understanding the problem — do not reference the problem's specific features during construction. The roster's only loss function is _maximize spread_.

This is farthest-first traversal applied to domain space. It works because:

- Mechanical pairwise distance comparisons are easier and more verifiable than expert "this field is structurally adjacent to that one" judgments
- Building blind to specific problem features prevents substrate bias from collapsing lens diversity
- The procedure has a natural stopping rule: when no new candidate is both loosely relevant AND meaningfully distant, the roster is done — no arbitrary count
- It maximizes coverage of the unknown problem space without requiring you to know in advance which features will matter

The structural-feature decomposition (Step 1) is still useful — but it's used for the **loose relevance gate** during Step 2 and for **post-hoc testing** of returned hypotheses, NOT as the generator of lens candidates.

### Operational test for isomorphism vs analogy (post-hoc, applied to picked lenses)

Once a lens is in the roster, you can test whether it's actually generative by asking:

1. **Name the specific shared object** between the lens's central objects and one of your problem's structural features (a stochastic matrix, a partial order, a sheaf, a phase boundary). If you can only name a metaphor ("both are like networks"), it's analogy — note this but don't necessarily reject; max-distance lenses sometimes produce surprising matches you didn't predict.
2. **Name one theorem or method the lens has about that object that the substrate doesn't already use.**
3. **Would a practitioner of the lens field recognize my problem as "their kind of problem" within 30 seconds?** This is the strongest signal.

These tests are POST-HOC quality checks on a roster generated by Step 2's max-distance walk. They are NOT the generator. Confusing the test with the generator is the failure mode.

## Procedure

### Step 0 [MANDATORY] — Triage (the go/no-go gate)

Answer all 4 questions in writing before doing anything else:

1. What is the one-sentence problem? (If you can't write it, ask the user.)
2. What's the user's success criterion? (If you can't state it, ask.)
3. What cheaper method was tried first (single Agent, direct reasoning, paper search), and why was it insufficient?
4. Does the problem have at least one **concrete noun** (system, dataset, domain) AND at least one **concrete constraint or known failure**?

If question 4 is no, the input is too vague — STOP and ask the user one clarifying question. Do not enter Step 1 with a content-free problem. The smallest dangerous input is "I'm stuck on this, what am I missing?" — 10 words, hits two trigger phrases, produces 12 confabulated hypotheses about a problem nobody stated.

### Step 1 — Frame the problem as math objects (LOOSE)

Strip surface vocabulary. Write a structural feature list as a **visible markdown bullet list**. This is used for two things only: (a) the "somewhat relevant" gate in Step 2, and (b) post-hoc testing of returned hypotheses in Step 9. **It is NOT the generator of lens candidates** — that's the central mistake.

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

### Step 2 [MANDATORY] — Build the lens roster by greedy max-distance walk

This is the core generative step. **Build the roster as a separate task from understanding the problem.** Do NOT consult Step 1's structural features during this step except as a loose relevance gate.

**Procedure:**

```
roster = []
seed = pick any domain that is "somewhat relevant" to the problem
       (relevance gate is intentionally loose — anything that could
        plausibly say SOMETHING about the problem qualifies)
roster.append(seed)

while True:
    candidate = the field that is BOTH:
       (i)  somewhat relevant to the problem (loose gate), AND
       (ii) maximally far from EVERY domain already in roster

    if no candidate satisfies both constraints:
        STOP — the roster is complete

    roster.append(candidate)

    if len(roster) >= ceiling:  # default 12, hard 15
        STOP
```

**Distance dimensions** (all of these matter, not just one):

- Vocabulary: would a glossary from field A be understood by an undergrad in field B?
- Methods: do they share methodology (e.g. "we both run regressions") or have entirely different toolchains?
- Training paths: would a PhD in A have ever taken a course in B?
- Citation networks: do papers in A ever cite papers in B?
- Conferences / venues: do practitioners ever attend the same meetings?
- "Seminar test": would a practitioner in A casually attend a seminar in B?

Two domains are **close** if a practitioner in one would casually attend a seminar in the other. Two domains are **far** if a practitioner in one would not understand the title of a paper in the other.

**The "somewhat relevant" gate is intentionally weak.** If you're rejecting candidates because "I don't see how X applies", you're applying the wrong filter — that question is for Step 9 (synthesis), not Step 2. Here you only ask: "could X plausibly say SOMETHING about this problem?" If yes, it passes.

**Why this works**:

- Greedy max-distance maximizes coverage of the unknown problem space without requiring you to know in advance which features will matter
- Mechanical pairwise distance comparisons are easier and more verifiable than expert "this field is structurally adjacent to that one" judgments
- Building blind to specific problem features prevents substrate bias from collapsing the lens diversity
- The natural stopping rule ("can't find anyone both relevant and distant") is more honest than an arbitrary count
- The structural decomposition from Step 1 is used as a _gate_ (relevance) and a _test_ (post-hoc isomorphism check) — never as the generator. This factoring is the central insight.

**Anti-pattern to avoid**: do NOT generate the roster by walking your structural-feature list and asking "what field has this object?". That's substrate-anchored search — the very thing this procedure replaces. If you find yourself doing it, stop and restart the walk from a non-substrate seed.

**Lower bound**: 4 lenses. Below this, the spread collapses — use a single deep Agent instead.
**Soft target**: 8-12 lenses.
**Upper bound**: 15. Above this, synthesis becomes painful and the marginal lens contributes little.

### Step 3 — Identify substrate (implicit, single)

The "substrate" is the user's actual problem domain — typically obvious and singular (e.g. "feline histiocytic sarcoma", "designing a new TypeScript type checker"). It is NOT a separate axis to be paired against lenses. Each agent in Step 8 will be told: "examine {substrate} from the perspective of {lens}". The substrate is constant; only the lens varies across agents.

### Step 4 [MANDATORY] — Walk the abstraction ladder (post-roster check)

After Step 2 produces a roster, walk the abstraction ladder and check coverage. This is a CHECK on the built roster, not a generative step.

If the problem has natural ordering axes — physical scale, temporal scale, OR **representational scale** (syntax -> semantics -> pragmatics -> meta) — list them and confirm your roster includes at least one lens at each level the problem touches.

For each scale, write **one sentence** explaining what a lens at that scale would SEE that lenses at other scales would miss. If a scale is uncovered, **return to Step 2 and run one more iteration constrained to "loosely relevant AND maximally distant from current roster AND addresses scale X"**. Add the resulting lens to the roster.

If you cannot find a lens that satisfies the additional constraint, mark the scale as an OPEN FEATURE in the synthesis doc — that uncovered scale is itself a research finding.

### Step 5 — "What scares it" pass (post-roster check)

What failure modes does this problem have? For each one, check whether the roster has a lens that specializes in defeating it:

- Tiny n -> Bayesian shrinkage, hierarchical models
- Train/deploy drift -> domain adaptation, covariate shift
- Multimodality -> MCMC mixing, optimization
- Asymmetric missing data -> survey statistics, missing-data theory
- Confounding -> causal inference, propensity scoring
- Reproducibility cliff -> meta-science, calibration theory
- Adversarial selection -> cryptography, game theory

If a critical failure mode has no lens, return to Step 2 for one more iteration constrained to that failure mode.

### Step 6 [MANDATORY] — Negative-space sanity check

After Step 2 + Step 4 + Step 5, count how many lenses in your roster come from **fields with no STEM overlap** (art, law, linguistics, trades, humanities, religious studies, sport, sedimentology, forensics, music theory, architecture, OR/queueing).

If fewer than **3** non-STEM lenses are present, the max-distance walk got stuck in a STEM cluster. **Return to Step 2 and restart the walk with a non-STEM seed**. STEM-only rosters are the canonical failure mode of cross-disciplinary work — if you don't see a humanities/art/non-quant field in your roster, you're playing it safe and reproducing what the field already knows.

### Step 7 [MANDATORY] — Pre-spawn checklist (READ-DO)

Before composing the sub-agent calls, fill out this checklist visibly. Announce it to the user. Do not spawn until every box is checked AND the user has had a chance to refuse.

```
PRE-SPAWN CHECKLIST
[ ] Roster size in [4, 15]: ___
[ ] Roster was generated by max-distance walk, NOT by feature-matching (K2)
[ ] No two roster members are "close" by the seminar test
[ ] At least 3 abstraction-ladder levels covered (Step 4)
[ ] At least 3 non-STEM lenses present (Step 6)
[ ] Critical failure modes have at least one defending lens (Step 5)
[ ] Each brief has CONTEXT block with all 5 sub-slots filled (K5)
[ ] All sub-agent blocks will be in ONE message (parallel) (K4)
[ ] Format string is verbatim from the template below
[ ] Cost announced: "Spawning N=__ agents in parallel, ~M minutes wall time."
[ ] User explicitly invoked the skill OR I have asked and received confirmation
[ ] Idempotency check: no prior polymath round exists for this problem (or user specified extend/replace)
```

### Step 8 [MANDATORY] — Spawn N parallel sub-agents

Use whatever sub-agent tool is available in your current environment (historically named `Agent` or `Task`). If only sequential spawning is available, state this limitation to the user and ask whether to proceed serially or abort.

**Launch all agents in a single message** with multiple tool-use blocks. Sequential dispatch is the [K4] silent failure.

Each agent gets a **self-contained brief** (it has zero context from this conversation). Each agent embodies ONE roster member (a lens) and examines the substrate from that perspective.

```
You are a polymath researcher with deep expertise in {LENS} approaching a problem outside your usual domain.

{ONE-LINE PROBLEM STATEMENT}

CONTEXT (self-contained — assume no prior knowledge):
- PROBLEM NUMBERS: {specific data points with units}
- PRIOR FINDINGS: {quote exact text or cite source}
- WHAT'S BEEN TRIED: {prior attempts and why insufficient}
- CONSTRAINTS: {what cannot be assumed/done}
- DEAD ENDS / NOT TO PROPOSE: {known failures}
- SUCCESS CRITERION: {what makes a hypothesis useful here}

FROM YOUR PERSPECTIVE AS A {LENS} EXPERT, propose 2-3 specific items that:
1. Use vocabulary, methods, or theorems native to your field
2. Re-describe the problem in your field's terms before answering
3. Name at least one technique your field uses for {closest-analogous-problem-in-your-field} that the substrate community probably hasn't tried

If the context is insufficient to ground a response, return `INSUFFICIENT CONTEXT: <what's missing>` instead of guessing. Do not fill gaps with plausible confabulation.

Format: Return ONLY the items, numbered, with a one-line title each. No preamble. Each item 3-5 sentences with a clear testable claim. For structural/re-framing fields (category theory, linguistics, philosophy of science, music theory), substitute "testable prediction" with "re-description of the problem in your field's native vocabulary, plus what that re-description makes visible".
```

**Hard rules for the brief:**

- If any of the 5 CONTEXT sub-slots is empty, justify why in a comment OR rewrite. Empty sub-slots produce confabulation.
- Total context block <=3KB per brief — pre-summarize substrate data into a shared block reused verbatim across all agents; only the {LENS} identity varies.
- **PII / clinical data**: before inlining clinical, patient, or identifying data, check whether it's safe to replicate N times. Prefer handles or citations over full records unless the user explicitly confirms.
- The {ONE-LINE PROBLEM STATEMENT} and CONTEXT block should be **identical** across all N briefs.

### Step 9a — Quality gate (triage returned briefs)

Before synthesis, check each returned brief:

- Matches the format (numbered items)?
- > =2 items returned?
- Names specific methods, not vague gestures?
- Returned `INSUFFICIENT CONTEXT`? -> its lens is unusable, do NOT include in synthesis
- Pair-wise: any two briefs with >80% lexical overlap? -> flag as correlation failure (the max-distance walk failed to actually distance them)

If <60% of agents produced usable output, do NOT synthesize. Report the failure to the user, name which abstraction levels / failure modes / non-STEM lenses ended up uncovered, and ask whether to re-spawn the failed lenses.

### Step 9 [MANDATORY] — Synthesize into a landscape doc

Use this template verbatim. Free-prose synthesis is [K6] failure — averaging happens by accident.

```markdown
# {Problem slug} — polymath landscape, {YYYY-MM-DD}

## Roster

| #   | Lens | Distance from previous (1-10) | Status |
| --- | ---- | ----------------------------- | ------ |

{one row per lens, in the order they were added by the max-distance walk}

## Convergent hypotheses (>=3 lenses reached independently)

{For each: name + which lenses + the mechanism each cited.
ROBUSTNESS CHECK: list each converging lens's hidden assumptions. If assumptions overlap heavily, the convergence is a roster artifact, not robustness — flag as such.}

## Unique-lens hypotheses (exactly 1 lens reached)

{For each: name + which lens + why the other lenses missed it.
These are the highest-value outputs of the round.}

## Active disagreements

{For each pair of contradictory hypotheses: state both, predict what experiment would discriminate them. Do NOT resolve.}

## Open features

{Structural features from Step 1 that no lens addressed, OR abstraction-ladder scales the roster failed to cover — the genuinely-novel territory.}

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

### Termination

The workflow ends when the landscape doc is written to a file (suggested path: `results/polymath/YYYY-MM-DD-{problem-slug}/landscape.md`) AND presented to the user with the question:

> **"Which region of this map do you want to explore first?"**

Do not pick for the user. Do not start implementing a hypothesis without their selection. The skill produces a map, not a recommendation.

## Error states and fallbacks

| Failure                                                  | Action                                                                                                                                                                        |
| -------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Harness forbids parallel sub-agents                      | State limitation, ask whether to serialize or abort                                                                                                                           |
| Sub-agent tool renamed/missing                           | Use whatever the current sub-agent tool is named; if none exists, abort and tell the user                                                                                     |
| User interrupts mid-spawn                                | If <60% returned: do not synthesize, ask whether to resume; if >=60%: synthesize partial, flag uncovered scales/lenses explicitly                                             |
| Agent returns prose instead of format                    | Re-spawn that one lens with stricter brief; do not synthesize malformed returns                                                                                               |
| 3+ agents return INSUFFICIENT CONTEXT                    | The CONTEXT block was [K5] failure — fix it and re-spawn the failures                                                                                                         |
| All agents converge on same hypothesis                   | Could be robustness OR roster collapse. Run robustness check in synthesis template; if assumptions overlap, run a second round with a non-STEM seed for the max-distance walk |
| Max-distance walk gets stuck (can't find new candidates) | This IS the natural stopping rule — do not force it. A roster of 6 honestly-distant lenses beats a roster of 12 with 6 forced lenses                                          |
| Max-distance walk produces only STEM lenses              | Step 6 failure — restart with a non-STEM seed (humanities, art, religious studies, trades)                                                                                    |
| User re-invokes on same problem (idempotency)            | Check for prior `results/polymath/*` artifacts. If found: ask whether to extend, replace, or critique existing — do NOT silently re-spawn                                     |

## Self-application (meta-use)

This skill CAN be applied to itself, but only as a **failure-mode audit variant** — never as hypothesis generation. The recursion is sound for one level; beyond that, the lens roster necessarily degenerates because all meta-lenses share the substrate "documentation that programs a future executor".

**Meta-application rule**: when the substrate is a methodology document, run the max-distance walk with seeds from fields that study _artifacts-describing-themselves_: metalogic, type theory, legal self-amendment, ritual studies, IFS, quine theory, constitutional drafting, pedagogy of unteachable skills, aviation checklist science, API design. Walk the distance from there.

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

## Anti-patterns

- **Substrate-anchored roster generation**: walking your structural-feature list and asking "what field has this object?" -> produces feature-matched lenses biased toward what you already see. Use max-distance walk instead.
- **Roster-from-memory**: pulling 12 famous fields without doing the max-distance walk -> lenses cluster around the user's training distribution
- **STEM cluster collapse**: every lens lives in a quant-STEM field -> restart with a non-STEM seed
- **Scale clustering**: every lens lives at the same abstraction level -> run Step 4 explicitly
- **Loose output format**: agents return prose essays -> always specify format string verbatim
- **Sequential dispatch**: agents fire one at a time -> [K4] failure
- **Premature averaging in synthesis** -> defeats the entire point
- **Cargo-culting a prior round's roster** -> defeats the max-distance walk entirely
- **Confabulation from thin context**: empty CONTEXT sub-slots -> agents fluently invent
- **Triggering on debugging**: "I'm stuck on this regex" -> false positive, burns budget
- **Using the structural decomposition as a generator**: decomposition is for the relevance gate and post-hoc tests only

## Variants

Same workflow, different framing-question template:

- **Hypothesis generation** (default): "What might be true?"
- **Failure-mode audit**: "What could break? What are we missing?"
- **Data/normalization audit**: "What relationships, scaling, or confounders might we be passing wrong?"
- **Architecture critique**: "What's structurally weak about this design?"
- **Naming/framing search**: "What's a better vocabulary for this problem?"

Map user verbs to variants: "hypotheses/ideas" -> generation; "what could break / poke holes" -> failure-mode audit; "review/critique/challenge" -> architecture critique. Swap framing questions in Step 8; keep the rest of the methodology identical.
