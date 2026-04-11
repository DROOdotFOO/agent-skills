# autoresearch

Domain-agnostic autonomous experiment runner. Define an objective, a metric, and a verify command -- the agent iterates on mutable files, keeping improvements and discarding regressions. Git-as-memory, JSONL state tracking.

Inspired by [karpathy/autoresearch](https://github.com/karpathy/autoresearch) and [drivelineresearch/autoresearch-claude-code](https://github.com/drivelineresearch/autoresearch-claude-code).

## Status: MVP

## Install

```bash
cd agents/autoresearch
pip install -e ".[dev]"
```

## Usage

### 1. Initialize an experiment

```bash
# ML training
autoresearch init gpt-small \
  --objective "minimize validation bits-per-byte" \
  --metric val_bpb --direction lower \
  --verify "uv run train.py" \
  --mutable train.py --budget 300

# Noir circuit optimization
autoresearch init circuit-opt \
  --objective "minimize constraint count" \
  --metric constraints --direction lower \
  --verify "nargo info 2>&1 | grep 'Circuit size'" \
  --pattern '(\w+):\s+(\d+)' \
  --mutable src/main.nr --guard "nargo test"

# Solidity gas optimization
autoresearch init gas-opt \
  --objective "minimize gas usage" \
  --metric gas --direction lower \
  --verify "forge test --gas-report" \
  --pattern 'gas:\s*(\w+)\s+(\d+)' \
  --mutable src/Contract.sol --guard "forge test"
```

### 2. Run manually or autonomously

```bash
# Single run (you describe the change)
autoresearch run "increase learning rate to 0.01"

# Autonomous loop (Claude generates hypotheses)
autoresearch loop --iterations 20 --model claude-sonnet-4-6

# Infinite loop (runs until killed)
autoresearch loop
```

### 3. Check progress

```bash
autoresearch status
autoresearch dashboard
autoresearch dashboard --output dashboard.md
```

## How it works

The core loop:

1. **Hypothesis** -- Claude reads the objective, current best metric, results history, and mutable file contents, then proposes ONE focused change
2. **Apply** -- The change is applied to mutable files and committed
3. **Verify** -- The verify command runs (fixed time budget)
4. **Evaluate** -- Metric extracted from output via regex pattern
5. **Keep/Discard** -- If improved: keep commit. If worse/crashed: revert.
6. **Repeat** -- Agent sees updated history and generates next hypothesis

## Metric protocol

The verify command should output metrics in this format:

```
METRIC loss=0.523
METRIC accuracy=0.95
```

Custom patterns supported via `--pattern` regex (group 1 = name, group 2 = value).

## State

JSONL file (`autoresearch.jsonl`) tracking config and all run results. Git branch `autoresearch/<name>` for version control. Results survive across sessions.

## Tests

```bash
python -m pytest tests/ -v
```
