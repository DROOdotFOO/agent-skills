---
title: Weird ERC20 Token Behaviors
impact: CRITICAL
impactDescription: Assuming standard ERC20 behavior causes silent fund loss with fee-on-transfer, rebasing, and non-compliant tokens
tags: solidity, erc20, fee-on-transfer, rebasing, usdt, weird-tokens
---

# Weird ERC20 Token Behaviors

Protocols that integrate arbitrary ERC20 tokens MUST handle non-standard
behaviors. Assuming `transfer(to, amount)` delivers exactly `amount` to `to`
is the single most common integration bug.

## Fee-on-Transfer Tokens

**Tokens**: USDT (optional fee), PAXG (0.02%), STA (1% deflationary burn)

The contract receives less than `amount` after `transferFrom`.

INCORRECT:
```solidity
function deposit(IERC20 token, uint256 amount) external {
    token.transferFrom(msg.sender, address(this), amount);
    balances[msg.sender] += amount; // BUG: actual received < amount
}
```

CORRECT:
```solidity
function deposit(IERC20 token, uint256 amount) external {
    uint256 before = token.balanceOf(address(this));
    token.transferFrom(msg.sender, address(this), amount);
    uint256 received = token.balanceOf(address(this)) - before;
    balances[msg.sender] += received;
}
```

## Rebasing Tokens

**Tokens**: stETH, Ampleforth (AMPL), OHM, LIDO

Balance changes without any transfer. Caching `balanceOf` is unsafe.

INCORRECT:
```solidity
// Vault stores raw balance at deposit time
mapping(address => uint256) public shares;

function deposit(uint256 amount) external {
    stETH.transferFrom(msg.sender, address(this), amount);
    shares[msg.sender] = amount; // BUG: balance rebases daily
}

function withdraw() external {
    stETH.transfer(msg.sender, shares[msg.sender]); // stale value
}
```

CORRECT:
```solidity
// Use wrapped non-rebasing version
function deposit(uint256 amount) external {
    stETH.transferFrom(msg.sender, address(this), amount);
    uint256 wstAmount = wstETH.wrap(amount);
    shares[msg.sender] += wstAmount; // wstETH does not rebase
}
```

Alternative: implement share-based accounting (ERC4626 pattern) where user
balance is a proportion of total vault holdings, not a fixed amount.

## No-Return Tokens

**Tokens**: USDT, BNB (older versions)

`transfer()` and `approve()` return nothing instead of `bool`. Solidity's
ABI decoder reverts when expecting a bool that was never returned.

INCORRECT:
```solidity
require(token.transfer(to, amount)); // reverts for USDT
```

CORRECT:
```solidity
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
using SafeERC20 for IERC20;

token.safeTransfer(to, amount); // handles missing return
```

## USDT Approval Race

USDT requires setting allowance to 0 before changing to a new non-zero value.

INCORRECT:
```solidity
token.approve(spender, newAmount); // reverts if current allowance != 0
```

CORRECT:
```solidity
token.safeApprove(spender, 0);
token.safeApprove(spender, newAmount);
// Or better: use safeIncreaseAllowance
token.safeIncreaseAllowance(spender, newAmount);
```

## Flash-Mintable Tokens

**Tokens**: DAI, any ERC-3156 compliant token

Can mint arbitrary supply within a single transaction. Using `totalSupply()`
for pricing or voting power within a transaction is exploitable.

INCORRECT:
```solidity
function getPrice() public view returns (uint256) {
    return reserve / token.totalSupply(); // manipulable via flash mint
}
```

CORRECT: Use time-weighted values or oracle-based pricing that cannot be
manipulated within a single block.

## Tokens with Blocklists

**Tokens**: USDC, USDT (centrally administered)

Transfers to/from blocklisted addresses revert. This breaks:
- Vault withdrawals (user gets blocklisted, funds stuck)
- Liquidation flows (borrower blocklisted, position unliquidatable)
- Batch operations (one blocklisted address reverts entire batch)

Defense: use pull-over-push patterns. Let users claim rather than pushing
tokens to them. Separate claim step allows retrying with different address.

## Low-Decimal Tokens

**Tokens**: USDC (6), WBTC (8), GUSD (2)

Rounding exploits when math assumes 18 decimals.

INCORRECT:
```solidity
// Assumes 18 decimals -- 1e12x error for USDC
uint256 valueInUsd = amount * price / 1e18;
```

CORRECT:
```solidity
uint256 valueInUsd = amount * price / (10 ** token.decimals());
```

First-depositor attacks are amplified with low-decimal tokens because the
rounding error represents more value per unit.

## Multiple Entry-Point Tokens

**Tokens**: SNX (legacy proxy + current proxy), some upgradeable tokens

Same underlying balance accessible at two different contract addresses.
Double-counting risk in protocols that track tokens by address.

Detection: Check if `token.target()` or `token.implementation()` points
to a shared state contract.

## Detection Checklist

Run this checklist for every token integration:

| # | Check | Detect Signal | Risk |
|---|-------|---------------|------|
| 1 | Fee-on-transfer | `balanceOf(this)` after transfer != amount arg | Fund accounting error |
| 2 | Rebasing | Token known to rebase OR `balanceOf` changes without transfer events | Stale balance |
| 3 | No-return | Token predates ERC20 finalization (2017) | Revert on interaction |
| 4 | Approval race | Token is USDT-like | Approval transaction reverts |
| 5 | Flash-mintable | Token implements ERC-3156 | Price/governance manipulation |
| 6 | Blocklist | Token has `blacklist`/`blocklist` mapping | Stuck funds, DoS |
| 7 | Low-decimal | `decimals() < 18` | Rounding exploits amplified |
| 8 | Multiple entries | Proxy pattern with legacy address | Double-counting |

## Universal Defense

For protocols accepting arbitrary tokens, use a token whitelist with per-token
configuration flags:

```solidity
struct TokenConfig {
    bool feeOnTransfer;    // use balance-before/after
    bool rebasing;         // require wrapped version
    uint8 decimals;        // normalize math
    bool blocklist;        // use pull pattern
}
```
