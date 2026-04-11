---
title: Three-tier stratification and the isomorphism test
impact: CRITICAL
impactDescription: Explains why three-tier parallel roster building produces better spread than single max-distance walk, and how to distinguish isomorphism from analogy post-hoc
tags: methodology, roster-building, isomorphism, three-tier
---

# Core Insight: Three-Tier Stratification

Brainstorming domains gives you what's _culturally adjacent_ to the problem -- the wrong move, because adjacent domains share assumptions with the substrate. You need lenses whose **objects look the same as yours but whose intuitions are different**. That's isomorphism, not analogy.

But the _generative_ move that produces good lenses is NOT "look at my problem and find isomorphic fields". That anchors lens selection to the substrate's vocabulary -- the very bias the workflow exists to escape. The right generative move is **parallel max-distance walks at three relatedness tiers**, then composing each agent as a polymath expert who carries one domain from each tier:

> Spawn three roster-builder sub-agents IN PARALLEL. Each receives the same one-line problem statement and the same relatedness constraint vocabulary, but a different tier: **closely related**, **somewhat related**, or **vaguely related** to the substrate. Each runs its own greedy max-distance walk inside its tier. Then for each final agent, sample one domain from each of the three rosters and wrap them into a single polymath expert persona (a researcher / engineer / consultant / practitioner whose work requires non-routine judgment).

This is farthest-first traversal applied to domain space, stratified by relatedness. It works because:

- Parallel construction avoids the orchestrator leaking its own substrate intuitions into all three tiers (sequential construction lets later tiers drift toward the earlier ones)
- Stratifying by relatedness guarantees tier diversity -- the "close" tier gives deep leverage, the "vague" tier gives wild leverage, and the middle tier bridges them
- Mechanical pairwise distance comparisons are easier and more verifiable than expert "this field is structurally adjacent to that one" judgments
- Building blind to specific problem features prevents substrate bias from collapsing lens diversity
- The natural stopping rule survives: each tier walk stops when no candidate is both tier-appropriate AND meaningfully distant from the already-chosen members of its tier
- Composing agents as polymath experts (one trait per tier) models how real cross-disciplinary insight actually happens -- a person who does their day job in field A, trained originally in field B, and has a serious hobby in field C sees things a pure-A specialist cannot

The structural-feature decomposition (Step 1) is still useful -- but it's used for the **loose relevance gate** during Step 2 and for **post-hoc testing** of returned hypotheses, NOT as the generator of lens candidates.

## Tier band definitions

- **T_close** -- same-building-as-substrate fields. A practitioner could attend a substrate seminar and follow >70% of the talk. Shares vocabulary and at least one object with the substrate. Could probably publish in a substrate venue with moderate translation effort.
- **T_mid** -- different-building-same-campus fields. The practitioner could read a substrate abstract and guess roughly what the paper is about, but would need a glossary for the methods section. Shares methodology families or analogous objects but not vocabulary.
- **T_far** -- different-campus fields. The practitioner would not recognize the substrate as "their kind of problem" at first glance, but a structural correspondence exists if someone points it out. Non-STEM fields land here by default. Includes humanities, arts, trades, crafts, games, religious studies, law, sport, music theory, architecture -- anywhere that domain experts make thoughtful non-routine decisions but whose vocabulary and methods do not touch the substrate's.

## Distance dimensions

All of these matter, not just one:

- Vocabulary: would a glossary from field A be understood by an undergrad in field B?
- Methods: do they share methodology or have entirely different toolchains?
- Training paths: would a PhD in A have ever taken a course in B?
- Citation networks: do papers in A ever cite papers in B?
- Conferences / venues: do practitioners ever attend the same meetings?
- "Seminar test": would a practitioner in A casually attend a seminar in B?

## Operational test for isomorphism vs analogy (post-hoc)

Once a lens is in the roster, test whether it's actually generative:

1. **Name the specific shared object** between the lens's central objects and one of your problem's structural features (a stochastic matrix, a partial order, a sheaf, a phase boundary). If you can only name a metaphor ("both are like networks"), it's analogy -- note this but don't necessarily reject; max-distance lenses sometimes produce surprising matches you didn't predict.
2. **Name one theorem or method the lens has about that object that the substrate doesn't already use.**
3. **Would a practitioner of the lens field recognize my problem as "their kind of problem" within 30 seconds?** This is the strongest signal.

These tests are POST-HOC quality checks on a roster generated by Step 2's max-distance walk. They are NOT the generator. Confusing the test with the generator is the failure mode.
