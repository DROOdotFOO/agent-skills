---
title: Invariant Breaks
impact: HIGH
impactDescription: Conservation laws, state couplings, capacity caps, and view/write equivalences violated by code paths that bypass enforcement
tags: solidity, invariants, conservation, state-coupling, capacity-cap, view-write-divergence
---

# Invariant Breaks

An **invariant** is a relationship that must hold at every observable state
of the contract. Audits find bugs by enumerating invariants, then finding
the code path that violates them. Synthesized from pashov's invariant-agent
methodology (v3) plus the numerical-gap-agent's seam catalog.

## Step 1 — Map every invariant

Extract every relationship the contract relies on:

| Class                | Examples                                                                       |
| -------------------- | ------------------------------------------------------------------------------ |
| Conservation laws    | `sum(balances) == totalSupply`, `deposited - withdrawn == balance(this)`        |
| State couplings      | when `X` changes, `Y` must change too (e.g., `position.size` ↔ `position.margin`) |
| Capacity constraints | `require(value <= limit)` — list every writer of `value`                       |
| Interface guarantees | view function promises a value that the state-changing function honors         |
| Peg invariants       | `circulating ≤ backing`, `supply == collateral / price`                        |
| Epoch boundaries     | per-epoch values constant across the epoch                                     |

For each invariant, list **every function that modifies any term**. Missing
one function in this list is the audit failure.

## Step 2 — Break each invariant

### Round-trip breaks

`deposit(X) → withdraw(all)` should return at most `X`. Test with `1 wei`,
`type(uint256).max`, first deposit, last deposit. Anything > `X` is a profit
extraction loop.

### Path divergence

Multiple routes reach the same outcome but produce different states. Take
the profitable path:

```solidity
function withdraw(uint256 shares) external { ... }     // pays fee
function emergencyWithdraw(uint256 shares) external { ... }  // skips fee — same outcome, free path
```

### Commutativity breaks

`A.action → B.action` produces different state than `B.action → A.action`.
Control transaction ordering to extract value. MEV searchers automate this.

### Capacity-cap bypass

Enumerate **all** paths that increase a capped value — settlement, fee
accrual, emergency mode, admin ops, rebase, reward distribution. Find the
path that skips the cap check:

```solidity
function deposit(uint256 a) external {
    require(totalDeposits + a <= CAP, "cap");   // checked
    totalDeposits += a;
}

function _accrueRewards() internal {
    totalDeposits += pendingRewards;            // BUG: same variable, no cap check
}
```

### Stale-cache-after-mutation

A function caches `state.x`, calls a mutator that writes `state.x`, then
uses the cached pre-mutation value. Enumerate every cache-then-mutate-then-
use chain:

```solidity
function rebalance() external {
    uint256 cachedPrice = oracle.price();    // cache
    _settle(cachedPrice);                    // mutator: writes oracle data inside
    _pay(cachedPrice);                       // BUG: uses pre-mutation cache
}
```

The cache must be invalidated or re-read after the mutator.

### Reset-timer via secondary path

A function unconditionally updates a timestamp (`asset.timestamp =
block.timestamp`, `lastClaim`) that an adversary uses to repeatedly reset
a window (JIT, cooldown, lockup):

```solidity
function updatePosition(...) external {
    position.lastUpdate = block.timestamp;   // BUG: not gated on actual deposit
    // attacker calls updatePosition() with a no-op to reset their lockup
}
```

Every `updateTimestamp` must be gated on an explicit branch (the work
that justifies resetting the timer must actually happen).

### Mid-operation parameter mutation

Multi-block operations (lottery draws, vault deposits, swap settlements,
auctions) assume constant parameters. Find every setter callable while a
draw/settle/multistep is **active**; settlement reads current values, not
values captured at start:

```solidity
function commitDraw() external { drawSeed = keccak256(...); }
function settleDraw() external { ... uses currentFeeBps ... }
// setter callable mid-draw — admin changes fee between commit and settle
function setFeeBps(uint16 bps) external onlyOwner { currentFeeBps = bps; }
```

Snapshot the parameters into the operation struct at commit time.

### View vs write divergence

`queryX(inputs)` returns one value; `doX(inputs)` writes a different value
because a penalty/fee/accrual/cascade is omitted from the view. Off-chain
integrators trust the wrong number; on-chain comparisons see drift:

```solidity
function previewWithdraw(uint256 shares) external view returns (uint256) {
    return shares * totalAssets / totalSupply;       // BUG: omits exit penalty
}

function withdraw(uint256 shares) external returns (uint256) {
    uint256 gross = shares * totalAssets / totalSupply;
    return gross * (10_000 - exitPenaltyBps) / 10_000; // applied here
}
```

Enumerate every `preview*`/`quote*`/`get*` pair against the corresponding
write path. The bodies' math must match modulo state mutation.

### Partial-mint peg break

Stablecoin or pegged-share mints that **partially fail** leave a portion
of supply un-collateralized. Peg invariant `supply ≤ backing` silently
breaks until the next full mint cycle:

```solidity
function mint(uint256 amount) external {
    for (uint i; i < strategies.length; ++i) {
        try strategies[i].deposit(amount / N) { backing += amount / N; }
        catch { /* BUG: continue — but we still mint full amount */ }
    }
    _mint(msg.sender, amount);    // BUG: full mint even if a strategy failed
}
```

### Strand-value across emergency transitions

Emergency mode pauses normal flows but the cleanup path does not sweep
accumulated rewards/earnings; value generated in emergency is permanently
stuck. Find every emergency-pause that lacks a paired cleanup.

### Coupled state-price reads across mutating paths

Liquidation reads price and balance at different points in the same
transaction; price moves between the reads (oracle update, swap, hook)
and the liquidation pays the wrong amount.

## Numerical-gap seams

Some invariants only break under the interaction of precision and edge
cases:

### Precision × invariant

`totalShares == sum(userShares)` is true for every individual deposit, but
rounding loss on each deposit accumulates so that after N deposits the
invariant silently drifts. Find every invariant whose proof assumes
real-number arithmetic and exploit the integer slippage.

### Boundary × invariant

An invariant enforced in the body but violated when execution hits an
early-return, revert-skip, or zero-input fast path:

```solidity
function repay(uint256 amount) external {
    if (amount == 0) return;       // BUG: bypass — lastUpdate is now stale
    _accrue();                     // invariant-preserving update
    debt[msg.sender] -= amount;
    lastUpdate = block.timestamp;
}
```

### Three-way (precision × boundary × invariant)

```solidity
liquidationBonus = collateral * bonusBps / 10_000;
// At very small collateral, bonus rounds to zero → liquidators never trigger
// → invariant "unhealthy positions get liquidated" breaks
// → position becomes permanently un-liquidatable.
```

## Step 3 — Construct the exploit

For every broken invariant: what **initial state** is needed, what calls
**break it**, what call **extracts value**, who **loses**. State all four
or the finding is a LEAD.

## Output discipline

```
invariant:        the conservation law / coupling / equivalence you broke
violation_path:   minimal call sequence that breaks it
proof:            concrete values showing invariant holding before and broken after
```

## See also

- [vulnerabilities/asymmetry](asymmetry.md) — the asymmetric writer that
  forgets to update a coupled storage variable is a very common invariant break.
- [vulnerabilities/flash-loans](flash-loans.md) — flash loans amplify
  capacity-cap and round-trip violations.
- [vulnerabilities/oracle-manipulation](oracle-manipulation.md) — coupled
  state-price reads.
- [audit-workflow/methodology](../audit-workflow/methodology.md) — the
  invariant pass slots into Phase 3.
