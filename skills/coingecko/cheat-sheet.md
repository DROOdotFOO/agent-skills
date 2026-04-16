---
impact: HIGH
impactDescription: "Key API endpoints, conventions, date formats, and error codes"
tags: "coingecko,api,endpoints,errors"
---

## Key endpoints cheat sheet

```bash
# Current price
GET /simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true

# Market data with ranking
GET /coins/markets?vs_currency=usd&per_page=50&sparkline=true

# Coin metadata + market data
GET /coins/{id}?tickers=false&community_data=false

# Price by contract address
GET /simple/token_price/{platform_id}?contract_addresses=0x...&vs_currencies=usd

# Top gainers/losers
GET /coins/top_gainers_losers?vs_currency=usd&duration=24h

# Trending DEX pools
GET /onchain/networks/trending_pools?duration=24h

# Pool megafilter
GET /onchain/pools/megafilter?networks=eth&sort=h24_volume_usd_desc&reserve_in_usd_min=100000

# Global market cap
GET /global
```

## Common conventions

- **Coin ID resolution**: Use `GET /coins/list` or `GET /search` to map symbols to IDs
- **Auto-granularity for charts**: 1d = 5-min, 2-90d = hourly, 90d+ = daily (00:00 UTC)
- **Date formats**: ISO `YYYY-MM-DD` for most endpoints, `DD-MM-YYYY` for `/coins/{id}/history`
- **Latest daily data**: Available 10-35 min after midnight UTC

## Error handling

| Code | Meaning |
|------|---------|
| 401 | No API key |
| 429 | Rate limit exceeded |
| 10002 | Wrong auth method |
| 10005 | Endpoint requires higher tier |
| 10010 | Pro key on Demo URL (or vice versa) |
