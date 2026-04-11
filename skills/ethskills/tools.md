---
title: Ethereum Development Tools
impact: HIGH
impactDescription: Core tooling commands for smart contract development and debugging.
tags: ethereum, foundry, blockscout, abi-ninja, tools
---

# Ethereum Development Tools

## Foundry essential commands

```bash
# Project setup
forge init my-project
forge install OpenZeppelin/openzeppelin-contracts

# Build
forge build

# Test
forge test                     # run all tests
forge test -vvvv               # max verbosity (traces)
forge test --match-test "test_deposit"  # specific test
forge test --gas-report        # gas usage per function
forge test --fuzz-runs 10000   # more fuzz iterations

# Deploy
forge script script/Deploy.s.sol --rpc-url $RPC --broadcast --verify

# Interact
cast call $CONTRACT "balanceOf(address)" $ADDR --rpc-url $RPC
cast send $CONTRACT "transfer(address,uint256)" $TO $AMT --rpc-url $RPC --private-key $KEY

# Utilities
cast abi-decode "transfer(address,uint256)" $CALLDATA
cast sig "transfer(address,uint256)"  # -> 0xa9059cbb
cast 4byte 0xa9059cbb                 # -> transfer(address,uint256)
cast to-wei 1.5 ether                 # -> 1500000000000000000
chisel                                # interactive Solidity REPL
```

## Blockscout MCP

16 tools via Model Context Protocol (configured in `~/.mcp.json`).
For full reference with usage patterns, see the **blockscout** skill.

```
# Address info (balance, token holdings, ENS)
get_address_info(chain_id=1, address="0x...")
get_tokens_by_address(chain_id=1, address="0x...")
nft_tokens_by_address(chain_id=1, address="0x...")
get_address_by_ens_name(name="vitalik.eth")

# Transactions
get_transactions_by_address(chain_id=1, address="0x...")
get_token_transfers_by_address(chain_id=1, address="0x...")
get_transaction_info(chain_id=1, transaction_hash="0x...")

# Contracts
get_contract_abi(chain_id=1, address="0x...")
inspect_contract_code(chain_id=1, address="0x...")
read_contract(chain_id=1, address="0x...", function_name="totalSupply")

# Blocks & lookup
get_block_info(chain_id=1, block_number=20000000)
get_block_number(chain_id=1, timestamp="2024-06-01T00:00:00Z")
lookup_token_by_symbol(chain_id=1, symbol="USDC")
get_chains_list()
```

Common chain IDs: Ethereum (1), Polygon (137), Base (8453), Arbitrum (42161),
Optimism (10), zkSync (324), Gnosis (100), Scroll (534352).

## abi.ninja

Browser tool for interacting with any contract using just its ABI or
a verified address. No wallet connection needed for read calls.

Use cases:

- Quick contract inspection without setting up a project
- Testing function calls with different parameters
- Reading storage on any verified contract
- Generating calldata for multisig transactions

URL: `https://abi.ninja`

## x402 Protocol

Payment protocol for AI agents -- enables pay-per-request API access
using crypto. Useful for agent-to-agent commerce.

```typescript
// Client (payer)
import { createPaymentHeader } from "x402-js";

const header = await createPaymentHeader({
  amount: "0.001",
  currency: "USDC",
  chain: "base",
  recipient: serviceAddress,
});

// Server (payee)
import { verifyPayment } from "x402-js";
const valid = await verifyPayment(header);
```
