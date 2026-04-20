---
title: Circuit Audit Methodology
impact: CRITICAL
impactDescription: Systematic audit process for ZK circuits covering spec-to-constraint mapping, constraint completeness, and privacy analysis
tags: noir, audit, circuit, soundness, completeness, spec-compliance, privacy
---

# Circuit Audit Methodology

Systematic process for auditing Noir circuits. Unlike application security
where bugs produce incorrect outputs, ZK circuit bugs produce valid proofs
for invalid statements -- the prover can forge proofs that verifiers accept.

## 3-Phase Circuit Audit

### Phase 1: Spec-to-Constraint Mapping

For each specification requirement, identify the constraint(s) that enforce
it. Any spec requirement without a corresponding constraint is a soundness bug.

**Build a traceability matrix:**

```
| Spec Requirement | Constraint Location | Enforced By | Test Exists? | Gap Risk |
|---|---|---|---|---|
| "Balance cannot go negative" | circuits/transfer.nr:28 | u64 cast + assert(b >= w) | Yes | -- |
| "Only owner can spend note" | circuits/spend.nr:45 | nullifier includes owner key | Yes | -- |
| "Total supply is conserved" | circuits/mint.nr:?? | MISSING | No | CRITICAL |
```

Process:
1. List every guarantee from documentation, comments, and README
2. For each guarantee, locate the exact constraint (assert, type cast, or arithmetic relation)
3. If a guarantee has no constraint, flag as CRITICAL gap
4. If a constraint has no test, flag as HIGH risk

### Phase 2: Constraint Completeness Scan

Verify that no value flows through the circuit without adequate constraints.

**Completeness checklist:**

- [ ] Every `unconstrained fn` return value is constrained in calling code before use
- [ ] Every oracle output is anchored to verifiable state (merkle proof, public input cross-check)
- [ ] Every Field subtraction has underflow protection where integer semantics are assumed
- [ ] Every `as u32/u64` cast is justified (not gratuitous -- each adds ~64-128 constraints)
- [ ] Every public input is minimized (no unnecessary information leakage)
- [ ] Nullifier derivation includes owner key AND unique note identifier
- [ ] No hash computation happens in unconstrained context (hashes MUST be constrained)
- [ ] Division hints verify: `a == b * quotient + remainder AND remainder < b`
- [ ] Array search hints verify: `arr[found_index] == target`
- [ ] Sorting hints verify: `sorted[i] <= sorted[i+1]` for all i, plus multiset equality

**For each unconstrained function, verify the compute-then-verify pattern:**

```noir
// INCORRECT: using unconstrained result without verification
unconstrained fn find_sqrt(x: Field) -> Field { /* ... */ }

fn main(x: Field) {
    let root = find_sqrt(x);
    // BUG: root is completely unconstrained -- prover can return anything
    assert(root > 0); // This does NOT verify it is actually a sqrt
}

// CORRECT: constrain the relationship
fn main(x: Field) {
    let root = unsafe { find_sqrt(x) };
    assert(root * root == x); // Verifies the claimed sqrt IS correct
}
```

### Phase 3: Privacy Analysis

Enumerate what an observer can learn from public inputs and outputs.

**For each public input/output:**

1. What information does it directly reveal?
2. Can private inputs be derived from public outputs? (small-domain attack)
3. Are there timing or size side channels?

**Small-domain brute-force check:**

If a private input has a small domain (age 0-150, boolean, enum with <1000 values),
and a public output is derived from it (even via hash), an observer can compute
all possible outputs and match:

```
// VULNERABLE: private age hashed as public commitment
// Attacker computes hash(0), hash(1), ..., hash(150) and matches
let commitment = std::hash::pedersen([age as Field]);
```

Defense: add high-entropy randomness to any commitment over small-domain values.

**Circuit fingerprinting check:**

If different code paths produce different constraint counts (visible in proof
metadata), an observer can determine which path was taken:

```noir
// VULNERABLE: if-else produces different constraint counts
if secret_flag {
    // 100 constraints
} else {
    // 50 constraints -- observer knows which branch by proof size
}
```

Defense: pad both branches to equal constraint count, or use branchless
arithmetic (select via multiplication).

## ZK-Specific Rationalizations to Reject

| Rationalization | Why It Is Wrong | Required Action |
|---|---|---|
| "The unconstrained function computes it correctly" | The prover controls unconstrained execution completely. A malicious prover returns whatever value benefits them. | Verify EVERY unconstrained output with a constraint that checks the claimed relationship. |
| "Field arithmetic works the same as integers" | Field wraps modulo p (~2^254). `5 - 10` is not `-5`, it is `p - 5` (a huge positive number that passes `> 0` checks). | Cast to bounded integer (u64) before any comparison that assumes non-negative semantics. |
| "The public input is just a hash, so the preimage is private" | Any input with fewer than ~2^80 possible values can be brute-forced against a hash. Ages, balances under $1M, booleans, small enums -- all vulnerable. | Add high-entropy salt/randomness to commitments. Verify the domain size exceeds brute-force threshold. |
| "Range checks are expensive so we will skip them" | A single unchecked value in a constraint system can break soundness entirely. The prover provides a field element that wraps around, bypassing all downstream logic. | Every value that participates in comparison or branching logic needs range verification. Budget constraints for this. |
| "The oracle is trusted" | In ZK, the prover IS the oracle for their own private data. There is no trusted oracle -- only constrained verification of claimed values against public state. | Anchor every oracle value to verifiable public state (merkle inclusion proof, cross-check against public input). |

## Audit Output Format

```
## Circuit Audit: [Circuit Name]

### Spec Coverage
| Requirement | Constraint | Status |
|---|---|---|

### Completeness Gaps
[List of unconstrained values, missing verifications]

### Privacy Findings
[List of information leaks, small-domain vulnerabilities]

### Soundness Findings
[List of forgeable proof scenarios with concrete attack]

### Constraint Budget
| Component | Constraints | Notes |
|---|---|---|
```

## Relationship to Other Security Files

- [oracle-safety.md](oracle-safety.md) -- detailed patterns for constraining oracle outputs
- [privacy.md](privacy.md) -- detailed privacy leak patterns and mitigations
- [aztec-contracts.md](aztec-contracts.md) -- Aztec-specific security (nullifiers, notes, MEV)
- [../circuits/constrained.md](../circuits/constrained.md) -- constraint optimization patterns
- [../circuits/unconstrained.md](../circuits/unconstrained.md) -- compute-then-verify patterns
