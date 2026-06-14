---
title: Attack Vector Database
impact: HIGH
impactDescription: Curated detect/false-positive pairs for bleeding-edge attack vectors beyond the core vulnerability categories
tags: solidity, attack-vectors, eip-7702, cross-chain, precision, economic, proxy
---

# Attack Vector Database

Curated attack vectors not fully covered by the core vulnerability files
(reentrancy, access-control, oracle, flash-loans, mev). Each entry includes
a detection signal and false-positive criteria to reduce noise.

## Math / Precision Attacks

### Rounding Direction Exploitation

**Attack**: Protocol rounds in user's favor on both deposit and withdrawal,
allowing profit extraction through repeated small operations.

| Field | Value |
|---|---|
| Detect Signal | Division operations in deposit/withdraw without explicit round-down/round-up |
| Code Pattern | `shares = amount * totalShares / totalAssets` without specifying rounding |
| False Positive When | Protocol explicitly rounds against the user (round-down on deposit, round-up on withdraw) |
| Severity | MEDIUM-HIGH (depends on gas cost vs extractable value) |

INCORRECT:
```solidity
function deposit(uint256 assets) external returns (uint256 shares) {
    shares = assets * totalShares / totalAssets; // rounds down -- favors depositor when totalAssets > totalShares
}
```

CORRECT:
```solidity
function deposit(uint256 assets) external returns (uint256 shares) {
    shares = assets.mulDiv(totalShares, totalAssets, Math.Rounding.Floor); // always round against depositor
}
```

### Dust Accumulation

**Attack**: Repeated operations accumulate rounding dust that can be
extracted by the last withdrawer or a specific function.

| Field | Value |
|---|---|
| Detect Signal | Loops or repeated operations with division that discard remainders |
| Code Pattern | `for (...) { amount += total / count; }` where `total % count != 0` |
| False Positive When | Dust is explicitly tracked and handled (swept to treasury, added to next distribution) |
| Severity | LOW-MEDIUM (scales with operation frequency) |

## EIP-7702 Delegation Confusion `[EVOLVING]`

**Attack**: With EIP-7702, EOAs can delegate to contract code. This breaks
two common assumptions: (1) `msg.sender == tx.origin` means "is EOA", and
(2) `extcodesize(addr) == 0` means "is EOA".

| Field | Value |
|---|---|
| Detect Signal | `require(msg.sender == tx.origin)` or `extcodesize` checks used for EOA detection |
| Code Pattern | `require(msg.sender == tx.origin, "no contracts")` |
| False Positive When | The check exists solely to prevent reentrancy (not to identify EOAs) and a reentrancy guard also exists |
| Severity | HIGH (bypasses intended access restrictions) |

INCORRECT:
```solidity
// Intended to block contracts from calling
require(msg.sender == tx.origin, "no contracts");
// With EIP-7702, an EOA delegates to a contract that calls this -- passes the check
```

CORRECT:
```solidity
// If the goal is preventing reentrancy, use a reentrancy guard
// If the goal is preventing flash loan attacks, use time-delay or snapshot
// There is no reliable on-chain way to distinguish EOAs from contracts post-7702
```

## Cross-Chain Sandwich `[EVOLVING]`

**Attack**: Exploiting bridge message delays to front-run cross-chain
operations. Attacker observes a large swap message on the source chain's
bridge queue, then front-runs on the destination chain.

| Field | Value |
|---|---|
| Detect Signal | Bridge-received messages that execute swaps or large state changes without slippage protection |
| Code Pattern | `onMessageReceived(...)` that calls `swap(amount, 0)` (minOut = 0) |
| False Positive When | Message includes enforced slippage parameters set by the user on the source chain |
| Severity | HIGH (attacker profits from user's cross-chain swap) |

Defense: All cross-chain swap parameters (minAmountOut, deadline) must be
set by the user on the source chain and enforced on the destination chain.
Never allow the relayer or destination contract to determine acceptable slippage.

## Dirty Higher-Order Bits `[EVOLVING]`

**Attack**: Unchecked downcasts from larger to smaller types preserve
unexpected data in higher-order bits when using assembly, or silently
truncate in Solidity >=0.8.

| Field | Value |
|---|---|
| Detect Signal | Assembly blocks performing `and`, `shr`, or manual type narrowing |
| Code Pattern | `let x := and(calldataload(offset), 0xffffffff)` missing for uint32 extraction |
| False Positive When | Solidity safe casts are used (automatic overflow check in 0.8+) without assembly |
| Severity | MEDIUM-HIGH (can corrupt packed storage or bypass validation) |

INCORRECT:
```solidity
assembly {
    let addr := calldataload(4) // 32 bytes loaded, only 20 bytes are address
    // addr has 12 bytes of garbage in high bits if caller sends dirty data
    sstore(slot, addr)
}
```

CORRECT:
```solidity
assembly {
    let addr := and(calldataload(4), 0xffffffffffffffffffffffffffffffffffffffff)
    sstore(slot, addr)
}
```

## Storage Collision in Proxies

**Attack**: Unstructured storage slots in proxy patterns collide with
implementation storage variables, allowing one to overwrite the other.

| Field | Value |
|---|---|
| Detect Signal | Proxy patterns not using EIP-1967 standard slots; custom `sload`/`sstore` in assembly |
| Code Pattern | `bytes32 constant IMPL_SLOT = keccak256("custom.proxy.impl")` (non-standard) |
| False Positive When | EIP-1967 slots are used (`0x360894a...` for implementation, `0xb53127...` for admin) |
| Severity | CRITICAL (arbitrary storage write = full compromise) |

INCORRECT:
```solidity
// Implementation storage starts at slot 0
uint256 public totalSupply; // slot 0

// Proxy also uses slot 0 for something
bytes32 constant IMPL_SLOT = bytes32(uint256(0)); // COLLISION
```

CORRECT:
```solidity
// EIP-1967: implementation slot is keccak256("eip1967.proxy.implementation") - 1
// This is astronomically unlikely to collide with sequential storage
bytes32 constant IMPL_SLOT = 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc;
```

## Donation Attacks (Beyond ERC4626)

**Attack**: Any contract using `address(this).balance` or
`token.balanceOf(address(this))` for accounting is vulnerable to donation
manipulation. The attacker sends tokens/ETH directly to inflate the
contract's apparent balance.

| Field | Value |
|---|---|
| Detect Signal | `address(this).balance` or `token.balanceOf(address(this))` used in share/price calculations |
| Code Pattern | `pricePerShare = token.balanceOf(address(this)) / totalShares` |
| False Positive When | Contract uses internal accounting (tracked deposits) instead of balance queries for calculations |
| Severity | HIGH (share price manipulation, first-depositor variant) |

INCORRECT:
```solidity
function pricePerShare() public view returns (uint256) {
    return token.balanceOf(address(this)) / totalShares;
    // Attacker donates tokens -> inflates price -> next depositor gets 0 shares
}
```

CORRECT:
```solidity
uint256 internal totalDeposited; // internal accounting, immune to donation

function pricePerShare() public view returns (uint256) {
    return totalDeposited / totalShares;
}
```

Donation attacks also affect:
- Reward distribution contracts (`rewardPerToken = balance / stakers`)
- Fee collection (`collectedFees = balance - lastKnownBalance`)
- Any `selfdestruct` forcing ETH into a contract that checks `address(this).balance`

## Incomplete Signature Validation

**Attack**: EIP-712 signatures missing chain ID, contract address, or nonce
in the domain separator allow cross-chain replay or cross-contract replay.

| Field | Value |
|---|---|
| Detect Signal | `ecrecover` usage without EIP-712 domain separator, or domain separator missing `block.chainid` |
| Code Pattern | `keccak256(abi.encodePacked(amount, recipient, nonce))` without domain |
| False Positive When | Full EIP-712 domain with `name`, `version`, `chainId`, `verifyingContract` |
| Severity | HIGH (signature replay across chains or contracts) |

## Narrow-Int Sign Drop

**Attack**: `uint24`/`int24` round-trips drop the sign bit. Negative ticks
or signed offsets become huge positive values, corrupting downstream
tree-tick or interval math (Uniswap V3 / V4 tick logic, AMM range orders).

| Field | Value |
|---|---|
| Detect Signal | Casts between `uint24` and `int24`, or `int256` → `int24` without bounds checks |
| Code Pattern | `int24 tick = int24(someInt256);` near tick / range / interval logic |
| False Positive When | Cast is gated by an explicit range check that excludes the sign-bit edge |
| Severity | HIGH (silent tick corruption in concentrated-liquidity math) |

## Intermediate-Shift Overflow

**Attack**: `(x << shift) / y` overflows `uint256` when `shift` makes `x`
exceed type max — even though the divided result is safe. Construct
flash-loan-scale `x` that breaks the intermediate.

| Field | Value |
|---|---|
| Detect Signal | `<<` immediately preceding `/` where the shift width is data-dependent |
| Code Pattern | `(amount << 64) / target` with `amount` attacker-influenced |
| False Positive When | Shift width is a constant ≤ 64 and operand fits a small uint |
| Severity | HIGH (reverts of legitimate flows, or wrap if assembly `shl` is used) |

## Sole-Occupant Boundary

**Attack**: Strict-less-than guards on participant counts or pool sizes
exclude the single-occupant case. The intended distinguishing-from-zero
check is wrong (should be `<=`):

```solidity
if (participants > 1) { ... }  // BUG: single solo participant gets skipped
```

| Field | Value |
|---|---|
| Detect Signal | `<` / `>` against participant / pool / lender counts in distinguishing-from-zero context |
| False Positive When | `<` is intentional (e.g., enforcing minimum two-party operation) |
| Severity | MEDIUM (DoS at sole-occupant edge) |

## Cast-Wrap at Saturation

**Attack**: Down-casts `uint64((x << 64) / y)` wrap to near-zero when the
ratio approaches 1; at saturation utilization, fees and rates silently
collapse instead of being capped. Lending and rate-curve code is the
common locus.

| Field | Value |
|---|---|
| Detect Signal | Narrow downcast on a fixed-point ratio whose normal range approaches 1.0 |
| Code Pattern | `uint64 fee = uint64((x << 64) / y);` with `x ≈ y` |
| False Positive When | Result is explicitly clamped before the cast |
| Severity | HIGH (lender APR or vault fee silently goes to zero) |

## Truncated Interest Accrual

**Attack**: Lending utilization curves scaling by `rate / SECONDS_PER_YEAR`
produce zero accrual when `principal · rate < SCALE`. Borrowers pay
nothing across the period — repeatable, compoundable theft of interest.

| Field | Value |
|---|---|
| Detect Signal | Per-second accrual formula `principal * rate * dt / SCALE` with no minimum |
| False Positive When | Accrual is capped to a per-block minimum or rounded UP for debt |
| Severity | MEDIUM-HIGH (compounding free borrow on small principals) |

## Unsigned Subtraction Underflow

**Attack**: `unsigned a - unsigned b` underflows when `b > a` at insolvent
or edge positions; downstream code interprets the wrap-around as a huge
positive value. Walk every `a - b` where bounds aren't asserted.

```solidity
uint256 surplus = totalCollateral - totalDebt;  // BUG: insolvent → underflow before 0.8 / unchecked block
```

| Field | Value |
|---|---|
| Detect Signal | Subtraction in an `unchecked { ... }` block or pre-0.8 Solidity, between two attacker-influenced unsigned values |
| False Positive When | An explicit `if (b > a) revert/return` precedes the subtraction |
| Severity | CRITICAL when downstream value is used for distribution / payout |

## Wrong-Mask Bit Pack/Unpack

**Attack**: Bitmask constants in pack/unpack helpers silently clear or
preserve adjacent fields when miscalculated; downstream readers receive
zero for fields that should carry data. Verify every mask against the
bit layout it claims to extract.

| Field | Value |
|---|---|
| Detect Signal | Hex masks (`0xff...`) used in `and`/`or` operations on packed structs |
| False Positive When | The bit layout is documented and the mask matches the documented field width |
| Severity | HIGH (zero defaults can authorize, pass guards, or skip validation) |

## Divide-by-Edge-Value

**Attack**: Formulas `x / tickSpacing`, `x / config.value`, `x / decimals`
revert or zero when the edge case (1, 0) is permitted as input. Construct
an input where the divisor reaches the edge.

| Field | Value |
|---|---|
| Detect Signal | Division by a storage value writable by admin or user without `> 0` / `>= MIN` gating |
| False Positive When | Setter rejects edge values OR division is in `unchecked { ... }` (rare and itself a finding) |
| Severity | HIGH (DoS on critical flow if revert, silent corruption if zero result is consumed) |

## Bytes20 Truncation (Cross-Encoded Recipients)

**Attack**: Encoders packing a long sender — `bytes32` non-EVM address,
`address` + extra metadata — into a narrower `bytes20` output silently
truncate. Refunds and callbacks route to the truncated value. Common in
bridges and cross-chain messaging.

| Field | Value |
|---|---|
| Detect Signal | `bytes20(longerBytes)` cast where source can exceed 20 bytes (BTC bech32, Solana 32-byte, attacker-chosen length) |
| Code Pattern | `address recipient = address(bytes20(payload));` after `payload` was decoded from cross-chain message |
| False Positive When | Source format is enforced to exactly 20 bytes by an upstream validator |
| Severity | CRITICAL (funds routed to attacker-controlled truncated address) |

## ERC721 Hook Re-Entry

**Attack**: `safeTransferFrom` calls `onERC721Received` on the receiver
**before** the originating contract finalizes state. The receiver re-enters
and observes inconsistent mid-flow state. Same shape applies to ERC1155
hooks and Uniswap V3 mint callbacks.

| Field | Value |
|---|---|
| Detect Signal | `safeTransferFrom` / `safeMint` / `_safeMint` mid-flow with state writes still pending after the call |
| Code Pattern | NFT receiver hook fires before the originating contract sets `ownership[id] = newOwner` |
| False Positive When | A reentrancy guard wraps the entire flow OR all state writes complete before the safe transfer |
| Severity | HIGH (double-mint, ownership-races, stale balance reads) |

## Unrestricted External Call from Custody

**Attack**: A contract holding tokens or NFTs performs an external call
whose target and calldata are attacker-controlled. The attacker calls
back into the held-asset contract (`safeTransferFrom`) using the holding
contract's authority.

| Field | Value |
|---|---|
| Detect Signal | A contract that has approvals or holds NFTs makes a user-supplied `.call(...)`, `.delegatecall(...)`, or arbitrary `IXxx(target).foo(...)` |
| Code Pattern | "Multicall", "execute", "callback-router" patterns where target ≠ msg.sender |
| False Positive When | Targets are whitelisted to a fixed allow-list |
| Severity | CRITICAL (confused-deputy fund drain) |

## Unbounded Caller-Supplied Fee/Bonus

**Attack**: External entry-points accept a fee or bonus parameter without
an upper bound. Downstream economics assume reasonable values but the
caller sets arbitrary — draining or bricking the path.

```solidity
function liquidate(address user, uint256 bonusBps) external {
    // BUG: bonusBps capped only by uint256.max — caller picks any value
    uint256 bonus = collateral[user] * bonusBps / 10_000;
    payable(msg.sender).transfer(bonus);
}
```

| Field | Value |
|---|---|
| Detect Signal | `external` function accepts a `bps`/`fee`/`bonus`/`slippage` value used in payout math without a `<= MAX_*` check |
| False Positive When | Value is constrained against a stored max OR is the caller's own protective minimum (e.g., `minAmountOut`) |
| Severity | CRITICAL (drain via inflated bonus) |

## Approval Residual

**Attack**: `approve(out + fee)` paired with `consume(out - fee)` leaves
`2 · fee` of residual allowance per call. After N calls the spender holds
`N · 2 · fee` of unspent allowance — convert to fund theft via any path
that pulls from the residual.

| Field | Value |
|---|---|
| Detect Signal | `approve(token, X)` followed by a path that consumes less than X, with no `approve(token, 0)` cleanup |
| False Positive When | Allowance is reset to 0 (or to actual consumed amount) at the end of the flow |
| Severity | HIGH (cumulative theft scales with call count) |

## Same-Block Oracle Read

**Attack**: A wrapper reads an external oracle in the **same block** as a
write that touches the underlying pool. An attacker manipulates the
oracle in the prior block (V3 `slot0`, single-source feed) and the
wrapper accepts the manipulated value.

| Field | Value |
|---|---|
| Detect Signal | Oracle read inside a function that also performs a deposit / liquidation / settle in the same tx, without time gating |
| Code Pattern | `slot0` read, single-source feed read, or `latestRoundData` without round-id staleness check |
| False Positive When | The read uses an enforced minimum staleness window OR an averaged TWAP with sufficient window |
| Severity | CRITICAL (single-tx price-manipulation drain) |

## Quick Reference

| Vector | Core Signal | Severity | Category |
|---|---|---|---|
| Rounding direction | Division without explicit rounding mode | MEDIUM | Math |
| Dust accumulation | Loops with division discarding remainders | LOW-MEDIUM | Math |
| EIP-7702 confusion `[EVOLVING]` | `msg.sender == tx.origin` as EOA check | HIGH | Access |
| Cross-chain sandwich `[EVOLVING]` | Bridge message executes swap with no slippage | HIGH | MEV |
| Dirty higher bits `[EVOLVING]` | Assembly type narrowing without masking | MEDIUM-HIGH | Data |
| Storage collision | Non-EIP-1967 proxy slots | CRITICAL | Proxy |
| Donation attack | `balanceOf(this)` in price/share math | HIGH | Economic |
| Signature replay | ecrecover without EIP-712 domain | HIGH | Auth |
| Narrow-int sign drop | `int24` / `uint24` casts in tick math | HIGH | Math |
| Intermediate-shift overflow | `(x << shift) / y` with attacker-scale x | HIGH | Math |
| Sole-occupant boundary | `participants > 1` excluding the lone case | MEDIUM | Boundary |
| Cast-wrap at saturation | Downcast of ratio ≈ 1.0 | HIGH | Math |
| Truncated interest accrual | `principal · rate < SCALE` → 0 accrual | MEDIUM-HIGH | Math |
| Unsigned subtraction underflow | `a - b` with `b > a` in `unchecked` | CRITICAL | Math |
| Wrong-mask bit pack | Hex mask vs documented bit layout mismatch | HIGH | Data |
| Divide-by-edge-value | `x / tickSpacing` with edge admittable | HIGH | Math |
| Bytes20 truncation | `bytes20(longerBytes)` cross-chain encode | CRITICAL | Bridge |
| ERC721 hook re-entry | `safeTransferFrom` before state finalized | HIGH | Reentry |
| Unrestricted custody call | Token-holder makes user-supplied external call | CRITICAL | Custody |
| Unbounded caller fee | `external` accepts fee/bonus without cap | CRITICAL | Economic |
| Approval residual | `approve(out+fee)` + `consume(out-fee)` | HIGH | Token |
| Same-block oracle | Spot oracle read + write in one tx | CRITICAL | Oracle |
