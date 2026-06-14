---
title: Asymmetry Bugs
impact: HIGH
impactDescription: Bugs in the gap between two places that should match — paired functions, branches within a function, writers vs readers of the same storage variable
tags: solidity, asymmetry, paired-functions, branch-symmetry, state-coupling, audit-methodology
---

# Asymmetry Bugs

The bug is rarely in one wrong line. It is in what is **missing or different
across two places that should match**: deposit vs withdraw, native branch vs
ERC20 branch, user `mint()` vs admin `forceMint()`, view function vs the
write function it claims to mirror. Synthesized from pashov's asymmetry-agent
methodology (v3) and the related flow-gap / numerical-gap / trust-gap seams.

## Paired-surface inventory

For every contract in scope, enumerate the pairs and note `file:line` of
both sides:

| Class             | Pairs                                                                 |
| ----------------- | --------------------------------------------------------------------- |
| Operation pairs   | deposit ↔ withdraw, mint ↔ burn, lock ↔ unlock, stake ↔ unstake       |
| Encoding pairs    | encode ↔ decode, abi.encodePacked ↔ abi.decode                        |
| Lifecycle pairs   | request ↔ fulfill, commit ↔ reveal, open ↔ close, init ↔ teardown     |
| Walk pairs        | modify ↔ settle, view ↔ modify, simulate ↔ execute, pre ↔ post        |
| Variant pairs     | user `X()` ↔ admin `forceX()`, single `X()` ↔ batch `XBatch()`        |
| Branch pairs      | native vs ERC20, happy vs revert, first-time vs subsequent            |

This inventory is the work plan. Steps 1–5 below apply to every entry.

## Step 1 — Storage-write symmetry diff

For each pair, side-by-side, list every storage variable each side writes
(mark `=`, `+=`, `-=`, `push`, `delete`) and every variable each side reads.
Diff the lists. Surface:

- Same variable written by both, but in **non-mirror direction** — user variant
  sets `settleAmount = 0`, admin variant sets `settleAmount = totalBalance`.
- Variable written by one side but **not the other** — state coupling broken.
- Variable read by one but **not the other** — stale-read risk.
- Mirror functions that mutate **entirely different slot sets**.

The bug: developer copied structure but forgot to mirror one update.

INCORRECT:

```solidity
// user-facing function settles their own balance
function settle() external {
    pendingAmount[msg.sender] = 0;
    settledAt[msg.sender] = block.timestamp;
}

// admin variant for emergencies — missing settledAt update
function forceSettle(address user) external onlyOwner {
    pendingAmount[user] = 0;
    // BUG: forgot settledAt[user] = block.timestamp
    // Downstream check `if (settledAt[user] == 0) revert NotSettled()` now wrong.
}
```

CORRECT: mirror the entire state mutation set, or factor the body into one
internal helper called from both entry points.

```solidity
function _settle(address user) internal {
    pendingAmount[user] = 0;
    settledAt[user] = block.timestamp;
    emit Settled(user, block.timestamp);
}

function settle() external { _settle(msg.sender); }
function forceSettle(address user) external onlyOwner { _settle(user); }
```

## Step 2 — Branch-symmetry diff

For every function with an internal branch (`if/else`, sentinel-vs-real,
native-vs-ERC20, payable vs non-payable), per branch list: validation,
storage written, fee deducted, downstream call. Diff branches and find:

- Validation in A missing in B (skip-validation bug).
- Fee deduction in A missing in B (free path).
- Downstream call shape differs (one passes `amount`, other passes `msg.value`).
- One branch reverts on edge, other silently no-ops.

INCORRECT — the native branch forwards `msg.value` raw while the ERC20
branch deducts fee from `amount`. Downstream consumers assume pre-fee value
was paid:

```solidity
function transfer(address token, uint256 amount, uint256 fee) external payable {
    if (token == NATIVE) {
        require(msg.value == amount, "bad value");
        _settle(amount);                       // BUG: pre-fee
    } else {
        IERC20(token).safeTransferFrom(msg.sender, address(this), amount);
        _settle(amount - fee);                 // post-fee, mismatched
    }
}
```

## Step 3 — Storage-variable lifecycle audit

For each storage variable used across the contract:

1. Find **all writers**.
2. Find **all readers**.
3. Flag:
   - Variable **written but never read** → forgotten state.
   - Variable **read but never written** → defaults to zero silently (false
     gates pass, comparison-against-zero allows anyone).
   - **Multiple writers with different validation shapes** → exploit the
     weakest one.

## Step 4 — Admin-function variants

For every admin function, check if it is a variant of a user-side function
(`mint` ↔ `adminMint`, `swap` ↔ `forceSwap`, `pause`/`unpause` for any
guarded op, `set*` for parameters that gate user behavior):

1. Diff against the user-side function for missing manipulation guards
   (slippage, deadline, manipulation locks), missing input validation,
   asymmetric state updates, missing `emit`.
2. **The Beefy pattern**: `deposit()` had `onlyCompPeriods`, but
   `setPositionWidth()` and `unpause()` mirrored the same liquidity-
   rebalancing flow without that guard → user sandwiches drain TVL on
   admin parameter change.
3. For every admin parameter change that affects user-relevant state, ask:
   **can a user sandwich the admin transaction?** Devs under-test admin
   functions because they view them as "trusted actor only" and skip
   layered defenses.

INCORRECT:

```solidity
function deposit(uint256 amount) external onlyCompPeriods {
    _rebalance();  // protected by onlyCompPeriods
    _mint(msg.sender, amount);
}

function setPositionWidth(uint256 width) external onlyOwner {
    positionWidth = width;
    _rebalance();   // BUG: same flow, no onlyCompPeriods, sandwichable
}
```

## Step 5 — Bad symmetry (defensive checks that should not exist)

Redundant or over-restrictive checks introduce DoS:

- Two checks of the same invariant in adjacent functions where the second
  is now over-restrictive (e.g., `prepareBoxes` decrements counter,
  `redeemBoxes` re-checks `counter > 0` → permanent DoS once preparation
  finishes).
- Comments saying "safety check" — the safety claim is frequently wrong.
- Symmetric validation in functions that should be asymmetric.

## Cross-cutting seam bugs

Some asymmetries only surface when combined with other lenses:

### Access × economics seam

A function whose access guard is correct in isolation and whose economic
formula is correct in isolation — but the actor permitted by the guard
can systematically extract value through the formula:

```solidity
// onlyKeeper rebalance with amountOutMin = 0
function rebalance() external onlyKeeper {
    router.swapExactTokensForTokens(
        balance, 0, path, address(this), block.timestamp
    );
    // Guard is correct (only keepers), swap is "standard" — but the keeper sandwiches themselves.
}
```

### Economics × asymmetry seam

A paired formula whose two sides use **different price sources** — each
"reasonable" in isolation, exploitable together:

```solidity
function deposit() external { shares = price.spot() * amount; }   // spot
function withdraw() external { amount = price.twap() * shares; }  // TWAP
// User deposits at depressed spot, withdraws at recovered TWAP. Risk-free arb.
```

### Approval-residual asymmetry

`approve(out + fee)` paired with `consume(out - fee)` leaves `2·fee`
of residual allowance per call. After N calls the spender holds `N · 2 · fee`
of unspent allowance — convert to fund theft via any path that pulls from
the residual.

## Output discipline

For every asymmetry finding, state THREE things in the report:

```
pair_or_branch: which pair (deposit/withdraw, native/ERC20, admin/user, view/write) you compared
asymmetry:      the exact write / read / check / formula that's in one side but missing or inverted in the other
proof:          side-by-side citation with concrete state values illustrating the break
```

Without all three, it is a LEAD, not a FINDING. See
[audit-workflow/report-template](../audit-workflow/report-template.md).

## See also

- [vulnerabilities/invariant-breaks](invariant-breaks.md) — conservation
  laws and state couplings broken by asymmetric writers.
- [vulnerabilities/attack-vectors](attack-vectors.md) — bleeding-edge
  precision and seam patterns.
- [audit-workflow/methodology](../audit-workflow/methodology.md) — where
  the asymmetry pass slots into the 5-phase audit.
