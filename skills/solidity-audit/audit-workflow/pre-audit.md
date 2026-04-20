---
title: Pre-Audit Reconnaissance
impact: CRITICAL
impactDescription: Skipping reconnaissance means auditing without understanding the protocol's threat model, entry points, or archetype-specific risks
tags: solidity, audit, reconnaissance, entry-points, threat-model, protocol-type
---

# Pre-Audit Reconnaissance

Before reading a single line of code for vulnerabilities, build context.
Auditing without reconnaissance produces scattered findings and misses
systemic risks. Complete this phase before Phase 1 (Scoping) of the main
methodology.

## Entry-Point Classification

Classify every `external` and `public` function by access level. This maps
the attack surface before hunting bugs.

| Access Level | Definition | Risk Tier |
|---|---|---|
| OPEN | Anyone can call, no auth check | Highest -- adversarial input guaranteed |
| AUTH | Requires msg.sender validation (e.g., onlyOwner, role check) | Medium -- compromised key or logic bypass |
| ADMIN | Multi-sig, timelock, or governance-gated | Lower -- but admin compromise is real |
| INTERNAL | Only called by other contract functions (not directly callable) | Lowest -- but reachable via OPEN functions |

### Output Format

For each contract in scope, produce:

```
| Function | Visibility | Access Level | State Changes | External Calls |
|----------|-----------|--------------|---------------|----------------|
| deposit() | external | OPEN | balances++ | token.transferFrom |
| withdraw() | external | OPEN | balances-- | token.transfer |
| setOracle() | external | ADMIN | oracle addr | none |
| _updatePrice() | internal | INTERNAL | price | oracle.latestRoundData |
```

Use Slither to bootstrap this:
```bash
slither . --print function-summary
slither . --print entry-points
```

Then manually verify access levels -- Slither may miss custom modifiers.

## Protocol-Type Threat Profiles

Identify the protocol archetype. Each type has dominant attack vectors and
critical invariants. Audit effort should concentrate on the archetype's
known failure modes.

### Lending / Borrowing

**Adversaries**: Borrowers (escape debt), liquidators (force liquidation), oracle manipulators
**Dominant attacks**: Oracle manipulation for undercollateralized borrows, liquidation frontrunning, bad debt accumulation, interest rate manipulation
**Critical invariants**:
- Total borrows <= total collateral * LTV for every position
- Liquidation always profitable enough to incentivize liquidators
- Interest accrual is monotonic and cannot be gamed by timing
**Look first**: Oracle integration, liquidation math, interest model edge cases

### DEX / AMM

**Adversaries**: Sandwich bots, JIT liquidity providers, price manipulators
**Dominant attacks**: Sandwich attacks, JIT liquidity (adding/removing in same block), pool manipulation via flash loans, TWAMM exploitation
**Critical invariants**:
- x * y = k (or equivalent) holds after every swap
- LP share value is monotonically non-decreasing (excluding IL)
- Fees accrue correctly to LPs and protocol
**Look first**: Swap math rounding, fee accounting, price update mechanism, MEV exposure

### Yield Aggregator / Vault

**Adversaries**: First depositors (vault inflation), strategy manipulators
**Dominant attacks**: First depositor/vault inflation (ERC4626), strategy migration exploit, reward token manipulation, share price manipulation
**Critical invariants**:
- shares * pricePerShare = user's claim on underlying (always)
- Deposit then immediate withdraw loses at most rounding dust
- Strategy cannot extract more than its allocated capital
**Look first**: Share math (especially first deposit), strategy trust boundary, harvest timing

### Stablecoin

**Adversaries**: Depeggers, collateral manipulators, governance attackers
**Dominant attacks**: Collateral ratio manipulation, liquidation cascades, redemption bank runs, governance capture for parameter changes
**Critical invariants**:
- Backing ratio >= minimum at all times
- Redemption always possible at fair value (within tolerance)
- Peg mechanism has bounded response time
**Look first**: Collateral valuation, liquidation cascade scenarios, emergency shutdown paths

### Bridge

**Adversaries**: Message forgers, relayers, sequencers
**Dominant attacks**: Message replay across chains, sequencer censorship/reordering, finality assumption violations, validator collusion
**Critical invariants**:
- Every token minted on destination has a locked counterpart on source
- Messages are processed exactly once
- Finality assumptions match the weakest chain
**Look first**: Message validation, replay protection, finality guarantees, validator set trust

### Governance

**Adversaries**: Flash loan voters, proposal griefers, timelock bypassers
**Dominant attacks**: Flash loan voting power, proposal spam/griefing, timelock bypass via emergency functions, voter apathy exploitation
**Critical invariants**:
- Voting power snapshot precedes proposal (no same-block manipulation)
- Timelock delay cannot be bypassed
- Quorum cannot be reached with flash-borrowed tokens
**Look first**: Snapshot timing, voting power calculation, timelock enforcement, emergency paths

## Invariant Extraction

Before code review, extract invariants from documentation:

1. Read whitepaper/docs and list every stated guarantee
2. For each guarantee, formulate as a testable property
3. Check if a Foundry invariant test exists for it
4. Flag gaps: stated guarantees without corresponding tests are high-risk areas

```
| Guarantee (from docs) | Invariant (testable) | Test exists? | Risk if broken |
|---|---|---|---|
| "Users can always withdraw" | withdraw() never reverts for funded user | No | CRITICAL - fund lock |
| "Collateral ratio >= 150%" | sum(collateral) / sum(debt) >= 1.5 | Yes | CRITICAL - bad debt |
```

## Dependency Map

List all external dependencies -- these are trust boundaries:

```
| Dependency | Type | Trust Level | Failure Mode |
|---|---|---|---|
| Chainlink ETH/USD | Oracle | High (decentralized) | Stale price, wrong price |
| Uniswap V3 pool | DEX | Medium (manipulable short-term) | Price manipulation via flash loan |
| OpenZeppelin Ownable | Library | High (audited) | Upgrade to malicious version |
| Timelock (2 day) | Governance | Medium | Compromised admin key |
```

## Checklist

Before starting vulnerability hunting, confirm:

- [ ] All external/public functions classified by access level
- [ ] Protocol archetype identified and threat profile reviewed
- [ ] Invariants extracted from documentation
- [ ] Dependency map complete with trust levels
- [ ] Scope boundaries clear (which contracts, which functions)
