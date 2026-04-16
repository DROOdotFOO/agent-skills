---
impact: HIGH
impactDescription: "Complete reference for all 16 Blockscout MCP tools grouped by category"
tags: "blockscout,mcp,tools,reference"
---

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
