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

### Find and verify a token by symbol

Symbol collisions are rampant. Searching `USDG` on Robinhood Chain (4663) returns 50+
tokens sharing that exact symbol -- one real, the rest imposters, all tagged
`reputation: "ok"`. **Never trust `symbol` or `reputation` alone.**

```
1. direct_api_call(chain_id="4663", endpoint_path="/api/v2/tokens",
     query_params={"q": "USDG"})
   -> every matching token with holders_count, circulating_market_cap,
      exchange_rate, decimals, icon_url, type

   (lookup_token_by_symbol is the convenience wrapper; the raw endpoint returns
    the richer fields needed to disambiguate, and paginates.)

2. Confirm the real token -- the genuine one is the outlier on:
   - holders_count       real USDG: 18,836   imposters: <100
   - circulating_market_cap / volume_24h    populated only on the real one
   - exchange_rate       "1.0" for the real stablecoin; null for imposters
   - icon_url            present (CoinGecko-sourced)
   - decimals            expected value (real USDG = 6; most imposters = 18)

3. Pin the confirmed address_hash and use it for all follow-up calls.
   Canonical USDG on Robinhood Chain = 0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168
```

### Chain overview

Before drilling into an unfamiliar chain, pull its stats:

```
direct_api_call(chain_id="4663", endpoint_path="/api/v2/stats")
  -> native coin price, gas prices (slow/average/fast),
     total transactions / addresses / blocks
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

## Resilience: when a chain is flaky

High-traffic chains (Base 8453, Polygon 137 -- ~900M addresses each) blip under
load: heavy endpoints (tx history, token lists) intermittently 500 or time out
while `/api/v2/stats` stays fine. Work the ladder in order before giving up:

1. **Narrow the query.** Prefer targeted calls (by address, `?q=SYMBOL`, a single
   token's holders) over broad enumeration. Fetch only the page you need.
2. **Paginate deliberately.** Follow `pagination.next_call`; do not request giant
   ranges in one shot.
3. **Retry with backoff.** Transient 500/429/timeout -- retry a few times (the
   step above is often enough on the second attempt).
4. **Drop to JSON-RPC for read primitives.** If the REST endpoint stays down but
   you only need a primitive (block number, balance, an `eth_call`), use the
   JSON-RPC passthrough:

   ```
   direct_api_call(chain_id="8453", endpoint_path="/json-rpc", method="POST",
     json_body={"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1})
   ```

   This still routes through Blockscout, so it does not help when Blockscout
   itself is the outage.

5. **Fall back to an independent public RPC** (only for JSON-RPC primitives --
   public RPCs speak `eth_*`, NOT the Blockscout REST API, so they cannot replace
   `/api/v2/...` calls). Ping via `cast`/`curl`; these rate-limit aggressively, so
   rotate and keep calls sparse:

   | Chain | Free public RPC endpoints |
   |-------|---------------------------|
   | Base (8453) | `https://mainnet.base.org`, `https://base.llamarpc.com`, `https://base-rpc.publicnode.com`, `https://base.drpc.org`, `https://1rpc.io/base` |
   | Polygon (137) | `https://polygon-rpc.com`, `https://polygon.llamarpc.com`, `https://polygon-bor-rpc.publicnode.com`, `https://polygon.drpc.org`, `https://1rpc.io/matic` |

   ```
   cast block-number --rpc-url https://base.llamarpc.com
   cast balance 0xADDR --rpc-url https://polygon-rpc.com
   ```
