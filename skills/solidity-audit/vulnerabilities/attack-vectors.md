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
