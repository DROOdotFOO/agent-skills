---
impact: MEDIUM
impactDescription: "Common workflows for address checks, tx investigation, contract inspection"
tags: "blockscout,patterns,workflows"
---

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
