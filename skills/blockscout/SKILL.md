---
name: blockscout
description: >
  Blockscout MCP tool reference for on-chain data queries. Covers all 16 tools:
  address info, transactions, token transfers, NFTs, contract ABI/source,
  read-only calls, ENS resolution, and block data across 8+ chains.
  TRIGGER when: user asks about on-chain data, contract state, token balances,
  transaction history, ENS lookup, NFT holdings, or uses blockscout MCP tools.
  DO NOT TRIGGER when: user asks about crypto market prices or trading volume
  (use coingecko skill), or writing Solidity code (use solidity-audit skill).
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: blockscout, blockchain, onchain, mcp, ethereum, web3
---

# Blockscout MCP

On-chain data queries via Blockscout MCP server (already configured).
16 tools across address intelligence, transactions, contracts, and blocks.

## Chain support

**EVM-only.** Blockscout covers 90+ EVM chains. Not available for native Solana
or Tron -- use CoinGecko contract endpoints for token data on those chains.

**Solana via Neon EVM**: Chain 245022934 covers the Neon EVM layer on Solana
(EVM-compatible contracts deployed on Solana).

### Common chain IDs

| Chain | ID | Chain | ID |
|-------|----|-------|----|
| Ethereum | 1 | Arbitrum One | 42161 |
| Polygon | 137 | OP Mainnet | 10 |
| Base | 8453 | zkSync Era | 324 |
| Gnosis | 100 | Scroll | 534352 |
| Celo | 42220 | Mode | 34443 |
| Neon EVM (Solana) | 245022934 | Filecoin | 314 |

Default: Ethereum (1). Use `get_chains_list` to discover all 90+ supported chains.

## Tools by category

### Setup

| Tool | Description |
|------|-------------|
| `__unlock_blockchain_analysis__` | **Call first** -- provides instructions to the MCP host |
| `get_chains_list` | List all known chains with IDs |

### Address intelligence

| Tool | Description |
|------|-------------|
| `get_address_info` | Balance, ENS name, contract status, proxy info, token details |
| `get_address_by_ens_name` | Resolve ENS name to Ethereum address |
| `get_tokens_by_address` | ERC-20 token holdings with exchange rates and market cap |
| `nft_tokens_by_address` | ERC-721/404/1155 NFT holdings grouped by collection |

### Transactions

| Tool | Description |
|------|-------------|
| `get_transactions_by_address` | Transaction history with decoded parameters. Supports `age_from`/`age_to` time filtering |
| `get_token_transfers_by_address` | ERC-20 transfer history with time filtering |
| `get_transaction_info` | Full tx details: decoded input, token transfers, fee breakdown |

### Contracts

| Tool | Description |
|------|-------------|
| `get_contract_abi` | Retrieve ABI for verified contracts |
| `inspect_contract_code` | View verified source code and metadata |
| `read_contract` | Execute read-only (view/pure) contract functions |

### Blocks & tokens

| Tool | Description |
|------|-------------|
| `get_block_info` | Block metadata (timestamp, gas, tx count) |
| `get_block_number` | Map a specific date/time to a block number |
| `lookup_token_by_symbol` | Search for tokens by symbol or name |

### Raw access

| Tool | Description |
|------|-------------|
| `direct_api_call` | Call any curated Blockscout API v2 endpoint directly |

## Usage patterns

### Check an address

```
1. get_address_info(chain_id=1, address="0x...")
   -> native balance, ENS, contract status

2. get_tokens_by_address(chain_id=1, address="0x...")
   -> ERC-20 holdings with values

3. nft_tokens_by_address(chain_id=1, address="0x...")
   -> NFT collections owned
```

### Investigate a transaction

```
1. get_transaction_info(chain_id=1, transaction_hash="0x...")
   -> decoded input, transfers, gas, status

2. get_token_transfers_by_address(chain_id=1, address="0x...",
     age_from="2024-01-01", age_to="2024-12-31")
   -> token movements in date range
```

### Inspect a contract

```
1. get_contract_abi(chain_id=1, address="0x...")
   -> full ABI (JSON)

2. inspect_contract_code(chain_id=1, address="0x...")
   -> verified source code

3. read_contract(chain_id=1, address="0x...",
     function_name="totalSupply")
   -> call view function
```

### Map dates to blocks

```
1. get_block_number(chain_id=1, timestamp="2024-06-01T00:00:00Z")
   -> block number at that time

2. get_block_info(chain_id=1, block_number=20000000)
   -> block details
```

## Pagination

When a response includes a `pagination` field, use the exact tool call in
`pagination.next_call` to fetch the next page. Continue until all data
is gathered or a reasonable limit is reached.

## Error handling

If a tool returns 500 Internal Server Error, retry up to 3 times.

## See also

- `coingecko` -- market prices, volumes, DEX pools, trending tokens
- `sentinel` -- automated contract monitoring with alert rules
- `ethskills` -- framework selection, RPC providers, EIP/ERC standards
- `solidity-audit` -- smart contract security patterns and audit methodology
