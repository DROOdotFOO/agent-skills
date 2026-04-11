# Sentinel

On-chain contract monitor that watches deployed contracts for anomalous transactions. Uses the Blockscout API for transaction data.

## Install

```bash
pip install -e ".[dev]"
```

## Usage

### One-shot check

```bash
# Check a contract on Ethereum mainnet
sentinel check --address 0xdAC17F958D2ee523a2206206994597C13D831ec7

# Check on Polygon, from a specific block
sentinel check --address 0x... --chain 137 --since-block 50000000
```

### Continuous monitoring

Create a `sentinel.toml` config:

```toml
poll_interval_seconds = 300

[[contracts]]
address = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
chain_id = 1
name = "USDT"

[contracts.alert_thresholds]
large_transfer_eth = 100.0

[[contracts]]
address = "0x..."
chain_id = 137
name = "MyPolygonContract"
```

Then run:

```bash
sentinel watch --config sentinel.toml
```

### View alerts

```bash
sentinel alerts
sentinel alerts --limit 50
```

## Alert rules

- **large_transfer** -- value exceeds threshold (default 10 ETH)
- **ownership_change** -- transferOwnership or renounceOwnership called
- **contract_selfdestruct** -- selfdestruct wrapper method detected
- **unusual_method** -- method_id not in known set (opt-in)

## Supported chains

Ethereum (1), Polygon (137), Optimism (10), Arbitrum (42161), Base (8453), Gnosis (100), zkSync Era (324), Scroll (534352).

## Tests

```bash
pytest
```
