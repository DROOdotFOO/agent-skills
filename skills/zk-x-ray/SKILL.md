---
name: zk-x-ray
description: >
  Pre-audit report generator for ZK + EVM hybrid protocols (Noir circuits +
  Solidity verifier / oracle layers). Produces an x-ray report, a classified
  entry-points map, an invariant catalog with a Circuit↔Solidity Consistency
  section, a per-circuit map, and an EIP-readiness verdict.
  TRIGGER when: project has both `foundry.toml` (or hardhat config) AND a
  `Nargo.toml` workspace; user asks for "zk-x-ray", "audit zk", "audit zkp",
  "zk readiness", "pre-eip review", "circuit-solidity audit", or "zk
  pre-audit"; EIP/ERC draft is being prepared for submission and a hybrid
  Solidity + Noir codebase needs a structural readiness check.
  DO NOT TRIGGER when: protocol is Solidity-only (use solidity-auditor skill or
  pashov's x-ray); deep circuit-design questions without Solidity integration
  (use noir skill); general Ethereum tooling questions (use ethskills); when a
  full external audit is the goal rather than a pre-audit briefing.
metadata:
  author: DROOdotFOO
  version: "0.2.0"
  tags: zk, zero-knowledge, audit, noir, solidity, hybrid, eip, x-ray, pre-audit, ultrahonk, barretenberg
---

# zk-x-ray

Pashov's `x-ray` methodology (v2 — 2026-04-22 readiness-report evolution
with cross-linked invariants) adapted for ZK + EVM hybrids: Noir circuits +
Solidity verifier contracts + an oracle / registry layer that validates circuit
public inputs.

## What You Get

One invocation populates `[project-root]/zk-x-ray/` with:

- **x-ray report** -- protocol overview, ZK-aware threat model, attack surfaces, EIP-readiness verdict
- **entry-points map** -- Solidity entry points classified by access level (permissionless / role-gated / admin) with call chains
- **invariants catalog** -- guards + single-contract + cross-contract + economic + Circuit↔Solidity Consistency (CSC)
- **circuit map** -- per-circuit table covering public inputs (logical / physical / Solidity-expected / generated verifier `NUMBER_OF_PUBLIC_INPUTS`), hashing scheme, in-circuit signature checks, domain tags
- **architecture diagram** (optional SVG)

Plus a `parity-check.py` CI gate that verifies Noir circuit, generated verifier,
and Solidity expected public-input arities all agree -- the #1 silent-fail mode
in ZK + EVM hybrids.

## Why this skill exists

Pashov's `x-ray` covers Solidity-only protocols brilliantly. ZK + EVM hybrids
have a class of silent-fail modes that no Solidity-only audit catches:

1. **Public-input layout drift.** A circuit's `main()` adds a `pub` field; the regenerated verifier accepts the new layout; the on-chain `validatePublicInputs` length check still expects the old count -- every legitimate proof reverts. Worse: re-ordering of two same-typed `pub` fields silently swaps semantic meaning, count unchanged.
2. **Domain-tag mismatch.** Off-chain key registration computes a Pedersen / Poseidon hash with one domain tag; the in-circuit version uses another. The on-chain registry accepts the off-chain hash; every legitimate proof reverts at the registry check.
3. **Unpinned toolchains.** `bb` and `nargo` have multiple beta releases per quarter. A verifier deployed under one `bb` version may not be reproducible from the same circuit under a later version. Soundness fixes only propagate to deployed contracts if the team can rebuild the exact verifier they shipped.
4. **Cross-deployment proof replay.** ZK proofs do not bind to a chain or contract address unless the circuit explicitly commits them in a public input. Replay-resistance reduces to off-chain replay DBs + on-chain `submitter == msg.sender` checks -- easy to miss until you trace a proof through two Oracle deployments.

zk-x-ray's invariant catalog adds a Circuit↔Solidity Consistency (CSC) section
that calls out each of these explicitly with `On-chain enforced? Yes/No` flags.

## Tips

- **Start with the circuit-map.** The first place a hybrid protocol breaks is the circuit↔solidity boundary. If the public-input parity table has any drift rows, fix those before reading anything else.
- **Treat the EIP-readiness verdict as a gate.** Any High-impact finding open at submission grades the protocol EXPOSED regardless of test coverage. The verdict is opinionated by design.
- **Pair with `solidity-auditor` + `noir`.** zk-x-ray surfaces *what to look at*; the deep methodology for each side lives in those skills.

## See also

- `noir` -- ZK circuit design, constraint optimization, Aztec integration
- `solidity-auditor` -- Foundry-first audit methodology + vulnerability taxonomy for the Solidity side
- `ethskills` -- EIP / ERC standards lookup, RPC providers, framework selection
- `blockscout` -- on-chain data queries when validating deployment state

This skill **complements** all four. For Solidity-only projects, defer to
`solidity-auditor` plus pashov's public `x-ray`; for circuit-only design
questions, defer to `noir`. zk-x-ray's value is the seam where the two meet.

## Reading guide

| Working on | Read |
|------------|------|
| ZK threat profiles, adversary ranking, ZK invariant taxonomy | [references/zk-threats.md](references/zk-threats.md) |
| Output file structure, CSC invariant template, EIP-readiness verdict format | [references/templates.md](references/templates.md) |

## Pipeline

3 phases, sequential. `$SKILL_DIR` = the directory containing this `SKILL.md`
(resolve from the load path the same way pashov's x-ray does).

Track progress with TaskCreate before running -- create three tasks
(`Phase 1: Enumerate`, `Phase 2: Read & classify`, `Phase 3: Write outputs`),
mark exactly one `in_progress` at a time.

---

## Phase 1: Enumerate

Detect project layout. Two flavors:

- **Solidity-only**: `foundry.toml` or `hardhat.config.*` at root, no `Nargo.toml`. Fall back to pashov's x-ray methodology in this case -- this skill's value-add is for hybrid projects.
- **Hybrid (the target)**: `foundry.toml` + `circuits/Nargo.toml` (workspace) or `circuits/*/Nargo.toml` (single).

Run enumeration + parity check (single Bash call, sequential):

```bash
mkdir -p [project-root]/zk-x-ray && \
  bash $SKILL_DIR/scripts/enumerate.sh [project-root] && \
  python3 $SKILL_DIR/scripts/parity-check.py [project-root]
```

`enumerate.sh` outputs labeled sections: `=== Solidity Source ===`,
`=== Noir Circuits ===`, `=== Noir Public Inputs (logical) ===`,
`=== Noir Public Inputs (physical) ===`, `=== Generated verifier
NUMBER_OF_PUBLIC_INPUTS ===`, `=== Solidity expectedPublicInputCount ===`,
`=== Tests ===`, `=== Toolchain Pins ===`, `=== Git ===`.

`parity-check.py` produces a single table that consolidates the four
public-input arity sources (logical / physical / Solidity expected / generated
verifier `NUMBER_OF_PUBLIC_INPUTS`) into one row per circuit and exits 1 if any
drift is detected. **A drift exit is a P0 finding** -- it must be resolved
before the rest of the audit can proceed (the Oracle's input validation will
reject every legitimate proof, or worse, accept proofs against an off-layout
input blob).

In the same message (parallel), launch:

1. **Foundry coverage** (background): `cd [root] && forge coverage 2>&1 || forge coverage --ir-minimum 2>&1`. Don't wait.
2. **Circuit test run** (background): if `circuits/Nargo.toml` exists, `cd circuits && nargo test --workspace 2>&1`.
3. **Reference reads** (foreground, parallel):
   - `$SKILL_DIR/references/zk-threats.md` -- ZK-specific threat profiles
   - `$SKILL_DIR/references/templates.md` -- output templates
4. **Spec/EIP detection** (Glob): `**/{eip,erc,spec,whitepaper,protocol,architecture,README,THREAT*}*.{md,pdf}` excluding `node_modules/`, `lib/`, `target/`, `out/`, `cache/`, `zk-x-ray/`. If size-aware: ≤5 files & ≤300 lines each, read directly in Phase 2's parallel batch; else delegate to a sonnet subagent for structured extraction (same prompt as pashov's templates.md spec extractor).

Proceed to Phase 2 without waiting for coverage / nargo test.

---

## Phase 2: Read sources + classify

In **one message**, parallel-call:

### 2a. Solidity source reads

Same logic as pashov: ≤20 files -> direct Read calls; >20 files -> sonnet subagents
grouped by subsystem. Per-file extraction includes the standard pashov fields
(type, inheritance, roles, state vars, external calls, fund flows, guards,
delta-writes, enum/one-shot transitions) **plus**:

- **Public-input decoders**: every `_validate*Inputs(...)` / `decodePublicInputs(...)` function. For each, record the offset layout (e.g. `[0:32] = jurisdiction`, `[32:64] = providerSetHash`, ...). This is the on-chain side of the circuit↔solidity contract; the circuit side comes from 2b.
- **Hash schemes**: every `keccak256(abi.encode/encodePacked(...))` or call into `EIP712*` libraries. Note what is committed (chainid? this-address? msg.sender? caller-supplied param?).
- **Signature recovery**: every `ecrecover(...)` or wrapper. Note malleability protection (low-s check) and v handling.

### 2b. Circuit source reads

If `circuits/` exists, read every `circuits/*/src/main.nr` and `circuits/shared/src/lib.nr`
(plus any sub-modules). For each circuit, extract:

- **`main` signature**: every `pub` parameter with its type. This is the *logical* public input list. Count: `N`.
- **Constraint count and complexity hints**: any `assert` / `assert_eq` / `verify` calls.
- **Hashing primitives**: `pedersen_hash`, `poseidon`, `keccak256`, `SHA-256` -- whichever the circuit uses. Note the inputs.
- **In-circuit signature checks**: e.g. `secp256k1::verify_signature` or equivalent. Record which payload is signed.
- **Domain tags**: any string/byte-array constants used as separator inputs to hashes.
- **Submitter binding**: whether `submitter` is a public input AND whether it is committed in any in-circuit hash.

### 2c. Public-input ABI parity

If circuits have been compiled (`circuits/*/target/*.json` exists), parse each
target JSON and extract the `abi.parameters` array -- specifically the `visibility:
"public"` entries. The count of these is the **physical** public input count, not
the logical count. (Noir flattens arrays into individual field elements: a `pub
[Field; 8]` is 8 physical inputs, 1 logical input. UltraHonk's
`NUMBER_OF_PUBLIC_INPUTS` constant in the generated verifier reflects the
physical count.)

For each circuit produce a row:

| Circuit | Logical pub count (from `main.nr`) | Physical pub count (from target JSON) | Solidity expected count (from on-chain library) |
|---------|------:|------:|------:|

The skill flags any row where the Solidity expected count does NOT match the
logical count, OR where the physical count and the generated verifier's
`NUMBER_OF_PUBLIC_INPUTS` disagree. This is the most common silent-fail mode in
ZK + EVM hybrids: the circuit changes its `pub` arity, the regenerated verifier
accepts the new layout, but the Oracle-level `validatePublicInputs` length check
still expects the old count and rejects every legitimate proof.

### 2d. Entry-point grep scan

Same as pashov's x-ray (POSIX-portable single-line + multiline grep, exclude
interfaces/mocks/views/pures). Classify into permissionless / role-gated /
admin-only.

### 2e. ZK threat profile

Use [references/zk-threats.md](references/zk-threats.md) to assign threat profiles. Most ZK protocols are
hybrids of multiple types -- common combinations:

- **Verifier router + Oracle**: Solidity contract holds a registry of generated
  ZK verifier addresses and validates public inputs before forwarding to the
  selected verifier. (e.g. erc-xochi-zkp.) Adversaries: soundness-bug exploiter,
  cross-deployment replayer, registry-curation compromise.
- **Bridge with ZK proof of state**: classic bridge adversaries plus
  circuit-soundness adversary.
- **Privacy mixer**: nullifier-based; commitment tree integrity adversary plus
  classic merkle-root manipulation adversaries.
- **ZK rollup**: state-transition function in a circuit; adversaries include
  circuit soundness, sequencer compromise, validity-proof forgery.

State the protocol's classification explicitly: `Protocol classified as: ZK
[type] with [secondary] characteristics`.

### 2f. Invariant synthesis

Run pashov v2's invariant synthesis over the Solidity sources, **then** add the
ZK-specific §5 (Circuit↔Solidity Consistency). The synthesis is a reasoning pass
— no new tool calls except a batched Grep for Pass B write-site enumeration.

**Terminology.** A *guard* is a per-call precondition enforced at a single
callsite (e.g., `require(amount >= MIN)`). Guards are not falsifiable — the code
guarantees them locally. An *invariant* is a property that must hold globally
across any sequence of calls. Guards feed §1 (Enforced Guards reference) only;
properties lifted from guards or stated in NatSpec feed §2 / §3 / §4.

**NatSpec routing (run first).** For each `@invariant` tag or inline comment
asserting a global property (*"totalSupply always equals Σ balances"*,
*"fee never exceeds MAX_BP"*, *"only one active epoch"*), route DIRECTLY to §2
(or §3 / §4 if cross-contract or economic) by shape (Conservation / Bound /
Ratio / StateMachine / Temporal). Source tag: `NatSpec: Contract.sol:LN`. Do NOT
place developer-stated global invariants in §1 — §1 is per-call guard
predicates only.

**Walk order** (each step uses raw extraction data, not prior-step conclusions):

1. **Conservation scan.** For each function, find delta-write pairs where
   `Δ(A) = +expr` and `Δ(B) = -expr` in the same function body. Each matched
   pair is a candidate: `A + B = const` or `A == Σ B[key]`. Verify across ALL
   functions that write either variable — partial conservation splits into
   Yes/No rows. **Negative conservation:** if a function that *ought* to track
   a flow (flashloan, receive/forward, settle) has zero storage Δ, record this
   as a Conservation-negative finding. Absence of Δ is itself an observation.

2. **Guard extraction + lift (two passes).**

   **Pass A — Verbatim into §1.** Every `require` / `assert` / `if-revert`
   becomes a `G-N` row in §1. Quote the predicate verbatim with `file:line`.
   This is a mechanical dump of per-call preconditions — not falsifiable.
   Skip guards that reference only function parameters with no storage tie-back.

   **Pass B — Lift to global property.** For each guard, ask: *does this imply
   a property that must hold across any sequence of calls?*
   - If NO (transient parameter consumed by the function) → leave in §1 only.
   - If YES (persistent property — e.g. `require(amount >= MIN)` at deposit
     implies "every active position ≥ MIN"; `require(_fee <= 10)` at setter
     implies "fee ∈ [0, 10]") → rewrite as a global property, then locate ALL
     write sites of the constrained storage variable via Grep on the variable
     name. **Batch ALL write-site Greps for all lifted guards into a SINGLE
     parallel message.**
     - If ALL write sites enforce the equivalent guard → §2 Bound invariant
       with On-chain=**Yes**.
     - If ANY write site writes without the guard → §2 Bound invariant with
       On-chain=**No**, citing the unguarded write site as the gap. **This is
       the high-signal output** — the gap is simultaneously an invariant and a
       potential bug.

3. **Ratio scan.** Each storage write of form `A = B * C / D` where B, C, D are
   storage or function-scoped snapshots → record the ratio + snapshot ordering
   (before/after other state changes in the same function).

4. **State machine / one-shot scan.** For each enum/uint/address in
   `require(var == X); ... var = Y` patterns:
   - **One-shot latch** (no path back) → record (e.g., `setStrategy`).
   - **Togglable flag** (another function flips back) → NOT a state-machine
     invariant, skip.
   - **Cyclic state** driven by timing → record as cycle invariant.

5. **Temporal scan.** Each `block.timestamp` or `block.number` comparison
   against a storage variable (deadline, lastUpdate, lockPeriod). Note whether
   checked-then-updated (safe) or updated-then-checked (stale-read risk).

6. **Cross-contract scan.** External call where the return value feeds
   arithmetic or a storage write → record caller assumption + callee write
   sites. If the callee can change state independently, the assumption is
   unvalidated → §3 cross-contract invariant with On-chain=No. Both sides must
   be inside scope files. Include **setter-vs-invariant mismatches** where an
   admin setter writes a storage value without checking that existing
   invariants still hold.

7. **Economic derivation.** Check if any combination of §2 + §3 invariants
   implies a higher-order property. Each §4 row must cite the I-N / X-N IDs it
   derives from. If the chain has any On-chain=No source, §4 is also No.

**Verification gate (MANDATORY drop rules).**

- Conservation: confirm Δ-pair exists at cited lines (same function body).
- Guard (§1 row): confirm the require/assert/if-revert is verbatim from code.
- Guard lift (§2 row): confirm the lifted property references persistent
  storage. Confirm all write sites enumerated. If any write site lacks the
  guard and the row says Yes, the row is invalid.
- NatSpec: confirm the tag/comment exists verbatim at cited location AND
  asserts a global (not per-call) property.
- Ratio: confirm formula and snapshot ordering.
- StateMachine: both edges exist AND no reverse path (else drop as togglable).
- Temporal: comparison involves a storage variable.
- Cross-contract: both caller + callee sides inside scope.
- Economic: all referenced I-N / X-N IDs are themselves verified.
- If you cannot verify → drop the row. "Could not verify" is not a valid row.

### 2f-ZK. Circuit↔Solidity Consistency (§5 — unique to zk-x-ray)

After the pashov walk, add §5: Circuit↔Solidity Consistency (CSC). Each row
pairs a Solidity-side commitment with a circuit-side commitment that the proof
must satisfy:

| ID | Property | Solidity side | Circuit side | On-chain enforced? |
|----|----------|---------------|--------------|--------------------|
| CSC-1 | `proofType` constants match between Solidity library and circuit module | `ProofTypes.sol:9-19` | `circuits/shared/src/constants.nr` | Yes via length check, NO via value collision check (see CSC-3) |
| CSC-2 | Public input *layout* expected by Solidity matches circuit `main()` ordering | `_validate*Inputs:[offsets]` | `circuits/*/src/main.nr` `pub` order | NO -- only the count is checked; mis-ordered fields silently pass |
| CSC-3 | Hash domain tags committed in-circuit match domain tags expected by registries | `compute_signer_pubkey_hash` callsite | `circuits/shared/src/sig.nr` | NO -- commitments are equal-or-revert at the boundary, but mismatch only manifests when the registry rejects every legitimate proof |
| CSC-4 | `submitter` public input is bound in any in-circuit signature digest | `proofSubmitter != msg.sender` revert | `compute_payload_hash` includes `submitter` | Yes if both sides agree |

A CSC row is **the highest-signal output for ZK hybrids** -- ordering or
domain-tag drift between circuit and Solidity is the #1 silent-fail mode and
neither audit pass alone catches it.

---

## Phase 3: Write outputs

In **one message**, parallel-write:

1. **x-ray report** at zk-x-ray/x-ray.md -- top-level report. Sections per the templates reference:
   - Overview + scope table (separating Solidity contracts, circuits, generated verifiers, libraries)
   - Threat & Trust Model (using ZK-aware adversary ranking from the threats reference)
   - Attack surfaces — **MUST cross-link** to invariant block IDs (see below)
   - **§3 Invariants is a POINTER ONLY** — a single blockquote callout with
     counts (guards / single-contract / cross-contract / economic / CSC) and a
     strong link to the invariants.md output. Do NOT duplicate the table here. This was
     pashov v1 behaviour and is no longer correct.
   - **Pre-EIP Findings** -- if the project has an EIP / ERC draft, this section is required: concrete pre-submission action items, severity-tagged.
   - Verdict (FORTIFIED / HARDENED / ADEQUATE / FRAGILE / EXPOSED)
2. **entry-points map** at zk-x-ray/entry-points.md -- pashov-style classified entry points
3. **invariants catalog** at zk-x-ray/invariants.md — five sections:
   §1 Enforced Guards (Reference), §2 Inferred Single-Contract, §3 Inferred
   Cross-Contract, §4 Economic, §5 Circuit↔Solidity Consistency. **Use
   `#### G-N` / `#### I-N` / `#### X-N` / `#### E-N` / `#### CSC-N` heading
   blocks — NOT tables.** Heading anchors (slug `#g-1`, `#i-17`, `#csc-2`, …)
   are the target of cross-file markdown links from x-ray.md attack surfaces;
   inline `<a id>` anchors inside table cells do NOT work cross-file in
   VS Code. Each `G-N` block must include a `Purpose` line. Every inferred
   block MUST cite a concrete Δ-pair, guard-lift + write-sites, edge, temporal
   predicate, or NatSpec claim — drop blocks that cannot. Every cross-contract
   block must cite BOTH caller-side assumption AND callee-side write sites.
4. **circuit map** at zk-x-ray/circuit-map.md -- per-circuit table covering public-input parity,
   hashing scheme, in-circuit signature checks, domain tags. **This file is
   unique to zk-x-ray** and the deliverable that purely-Solidity audits miss.

### Cross-link requirement (Key Attack Surfaces ↔ invariants.md)

When writing Section 2 Key Attack Surfaces, cross-reference each surface
against the invariants.md blocks you just produced. If the surface's cited
`file:line` falls within the `Location` / `Derivation` / `Caller side` /
`Callee side` window of any `G-N` / `I-N` / `X-N` / `E-N` / `CSC-N` block,
append the matching IDs as bracketed markdown links immediately after the
surface title using LOWERCASE slug fragments:

```markdown
- **Surface name** &nbsp;&#91;[X-4](invariants.md#x-4), [I-17](invariants.md#i-17), [CSC-2](invariants.md#csc-2)&#93; — ...
```

Separate each surface bullet with a blank line. Surfaces that are purely
access-control or upgrade-ability concerns may be left unlinked — that is a
healthy signal, not a gap. Typical hit rate on non-trivial protocols: ≥70% of
surfaces link to at least one invariant. For ZK hybrids, attack surfaces
touching the prover / verifier / registry should almost always link to CSC-N
rows.

### Test existence vs. coverage execution (CRITICAL)

**Test presence** comes from Step 1 enumeration (`test_files`,
`test_functions`, `stateless_fuzz`, `foundry_invariant`, `echidna`, `medusa`,
`certora`, `halmos`, `hevm`, plus `nargo test` for circuits) — file-scan
results, always reliable.

**Coverage metrics** (`forge coverage`, circuit nargo test execution) require
installed toolchains and successful compilation. Failure can be unrelated to
test quality (missing deps, stack-too-deep, `bb` version drift).

Rules:

1. Use `test_files`/`test_functions` from Step 1 for ALL test existence
   claims. Never infer "no tests" from coverage tool failure.
2. If coverage fails but enumeration shows tests exist, report:
   `"[N] test files with [M] test functions detected; coverage metrics
   unavailable — [failure reason]"`.
3. In "Gaps", only flag missing categories (stateless_fuzz=0,
   foundry_invariant=0, echidna=0, …). Prioritize: missing stateful fuzz +
   formal verification for math-heavy financial logic is higher priority than
   missing fork tests. For ZK: missing circuit-level fuzz / formal proof of
   constraint soundness is high-priority — call it out explicitly.
4. Test presence and coverage metrics are independent signals — do not let
   coverage failure cascade into the threat model.

### Branch scoping

The git analysis is scoped to the **current branch only** (HEAD). All git
signals reflect commits reachable from HEAD — not other branches.

1. State the analyzed branch in the report header or git history section:
   `"Analyzed branch: \`[branch]\` at \`[commit]\`"`.
2. When describing fix commits from git history, describe them as what the
   **current branch code** does — not what a fix "changed" if you cannot see
   the before/after on this branch.
3. If the repo shape is `squashed_import` (1 commit), there is no meaningful
   evolution — state this and skip fix/hotspot analysis.

### Backwards-compatibility code detection

While reading source, watch for code that appears to be remnants of a removed
mechanism kept so the remaining codebase does not break. Common signals: empty
or trivial function bodies, state variables declared but never meaningfully
read or written, comments containing "deprecated" / "legacy" / "backwards
compat" / "no longer used".

Before classifying anything as backwards-compatibility, run **mandatory
verification checks** (batch all caller-check Greps into a SINGLE message):

1. **Caller check (REQUIRED).** No active callers in the current codebase.
   If it IS called from active code paths, it is current design, not BC.
2. **NatSpec/comment check (REQUIRED).** If code has NatSpec or inline
   comments explaining intentional behavior ("simplified for X mode",
   "by design", "intentionally zero"), this is documented intent, not BC.
3. **Interface obligation check.** A function returning defaults because an
   interface requires it AND actively called is current architecture.

Only classify as BC when (a) no active callers, (b) no documenting comments,
(c) git history shows the mechanism was removed.

Note BC code explicitly in Section 1 of the report so auditors know which
parts are retained for compatibility vs live functionality. Omit the
subsection if no BC code survives the verification gate.

Optional 5th file: if the project warrants a diagram, generate an architecture
SVG via the same generator flow as pashov's skill (port that script in if/when
the skill is upgraded beyond a draft).

### Verdict tier signals (ZK-specific overrides)

The pashov tier-calculation rules apply, with two ZK-specific additions:

- **Public-input parity:** any drift (CSC-2 / CSC-3 with On-chain=No) drops the
  verdict by one tier.
- **Toolchain pinning:** if `bb` and `nargo` versions are NOT pinned (no
  `.tool-versions`, `flake.nix`, or equivalent), drop one tier. Soundness fixes
  in `bb` only propagate if the team can reproduce the exact verifier they
  deployed; unpinned toolchains break this guarantee.

### Pre-EIP gate (additional, for EIP submissions only)

If `eip-draft*.md` or `erc-*.md` is present, the Verdict section MUST include a
"Pre-EIP punch list" with concrete action items in priority order. The skill is
opinionated: an EIP submission with any High-impact finding open is graded
EXPOSED regardless of the test/docs/access-control tier.

---

## Constraints

- Under 500 lines for the x-ray report. Compress overview + repo metadata before threat
  model, invariants, or findings.
- No fabrication. Say "could not determine" when uncertain.
- Single pass. No partial outputs.
- Vendor-neutral framing. Do not reference audit firms, contests, or bounty
  programs in the report itself.
- Solidity-only projects: defer to pashov's x-ray. State this and exit early.

---

Before doing anything else, print this exactly:

```
zk-x-ray
========
ZK + EVM hybrid pre-audit report generator.
Sources: pashov/skills/x-ray (methodology), tailored for Noir + Solidity hybrids.
```
