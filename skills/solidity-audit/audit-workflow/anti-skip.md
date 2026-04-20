---
title: Rationalizations to Reject
impact: HIGH
impactDescription: The most common audit failure is rationalizing away a real finding before fully investigating -- this anti-skip table prevents false negatives
tags: solidity, audit, anti-skip, discipline, false-negatives, proof-required
---

# Rationalizations to Reject

The auditor's biggest enemy is not complexity -- it is the tendency to
rationalize away suspicious patterns before fully investigating them. Every
rationalization below has led to missed vulnerabilities in real audits.

## Anti-Skip Table

| Rationalization | Why It Is Wrong | Required Action |
|---|---|---|
| "The admin is trusted" | Admins get compromised: key theft, social engineering, insider threat, nation-state attacks. Wintermute, Ronin, Harmony all lost admin keys. | Audit admin functions as if admin is hostile. Document all admin powers explicitly. |
| "Nobody would do that" | Attackers have unlimited time, financial incentive, and sophisticated tooling. If the code allows it, assume someone will do it. | Prove it is impossible on-chain, not just unlikely. |
| "That is too expensive to exploit" | Flash loans provide unlimited capital at zero cost. Gas costs drop over time. L2s make previously expensive attacks cheap. | Calculate actual exploit profit including flash loans. If profit > 0, it is viable. |
| "The frontend prevents that" | Contracts are called directly via etherscan, scripts, bots, and MEV bundles. Frontends are suggestions, not security boundaries. | Only on-chain validation counts. Treat every external function as if called by a raw transaction. |
| "Tests cover this" | Tests prove the happy path works. They rarely test adversarial inputs, state corruption, or malicious call ordering. | Check what the tests do NOT test. Missing test = likely bug hiding spot. |
| "It is only informational" | Informational findings combine into exploits. A missing event + a stale cache + a timing window = critical exploit chain. | Classify based on impact if chained with other findings, not in isolation. |
| "This follows the standard pattern" | Standard patterns (OZ, Uniswap) misapplied to novel contexts are bugs. A reentrancy guard on the wrong function, SafeERC20 on a non-standard token. | Verify the pattern's assumptions hold in THIS specific context. |
| "There is an upgradeability escape hatch" | Upgrade timelocks may be too slow to prevent exploit. Governance may not convene in time. Some exploits drain in one block. | Treat current code as final and unupgradeable for severity classification. |

## Proof-Required Discipline

Every finding at MEDIUM severity or above MUST include a `proof:` field
demonstrating the exploit with concrete values.

**FINDING** (has proof):
```
## [H-1] First depositor can steal subsequent deposits via share inflation

proof:
  1. Attacker deposits 1 wei -> receives 1 share
  2. Attacker donates 10000e18 tokens directly to vault
  3. pricePerShare = 10000e18 + 1 / 1 = 10000000000000000000001
  4. Victim deposits 9999e18 -> receives 9999e18 / 10000000000000000000001 = 0 shares
  5. Attacker withdraws 1 share -> receives all 19999e18 tokens
```

**LEAD** (no proof -- needs investigation, not a reportable finding):
```
## [LEAD] Possible share manipulation in vault deposit flow

The deposit function may be vulnerable to first-depositor manipulation
but the exact exploit path has not been verified.
```

Rules:
- No proof = LEAD, not FINDING. LEADs go in appendix, not findings section.
- Proof must include concrete values (amounts, addresses, block numbers).
- Ideally proof is a Foundry test. Minimum is a step-by-step trace with numbers.
- "Could be exploited" language is never acceptable for MEDIUM+.

## False-Positive Elimination Pass

After completing the vulnerability scan (Phase 2 + Phase 3), run this
elimination pass on every MEDIUM+ finding:

### For each finding:

1. **Trace the path**: Can an external caller actually reach this code with
   malicious input? Trace from entry point to vulnerable line.

2. **Check defenses**: Are there guards between the entry point and the
   vulnerability that prevent exploitation? (modifiers, require statements,
   access control, reentrancy guards)

3. **Construct exploit**: Write the actual attack transaction sequence.
   If you cannot construct it, the finding may be a false positive.

4. **Verify preconditions**: Does the exploit require conditions that cannot
   exist? (e.g., manipulating a Chainlink oracle requires >50% of nodes)

5. **Classify**:
   - **CONFIRMED**: Exploit constructed, preconditions achievable
   - **FALSE POSITIVE**: Defense exists that prevents exploitation (document which defense)
   - **NEEDS INVESTIGATION**: Path exists but precondition feasibility is unclear

### Weaponize Across Contracts

When a vulnerability is CONFIRMED in one contract:

1. Identify the vulnerable pattern (e.g., missing balance-before/after check)
2. Search ALL other contracts in scope for the same pattern
3. Report all instances as a single finding with multiple locations
4. If the pattern exists in a shared library, flag systemic risk

```bash
# Example: search for transfer without balance check
grep -rn "transferFrom" src/ | grep -v "balanceOf"
```

## Parallel Domain Decomposition

For large audit scopes (10+ contracts), structure the manual review as
parallel passes by attack domain. Each pass focuses on one vulnerability
class across the entire codebase:

| Domain | Focus | Key Patterns |
|---|---|---|
| Math/Precision | Rounding, overflow, division by zero, decimal normalization | `* / +` sequences, type casts, decimal conversions |
| Access Control | Missing checks, privilege escalation, role confusion | modifiers, msg.sender, tx.origin, delegatecall |
| Economic/Incentive | Flash loan exploits, MEV, game theory, oracle manipulation | price calculations, voting, reward distribution |
| Execution Trace | Reentrancy, call ordering, state corruption | external calls, callbacks, state reads after calls |
| Invariant Analysis | Protocol guarantees, accounting identities | totals, ratios, monotonicity properties |
| Periphery/Integrations | External contract assumptions, token behaviors, oracle trust | interface calls, token interactions, bridge messages |
| First Principles | Novel logic flaws not fitting categories above | business logic, edge cases, timing |

This decomposition prevents tunnel vision. A math-focused pass catches
precision bugs that a reentrancy-focused auditor overlooks, and vice versa.
