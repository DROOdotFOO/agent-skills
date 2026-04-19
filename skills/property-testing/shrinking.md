---
title: Shrinking and Debugging Failures
impact: HIGH
impactDescription: Without effective shrinking, property test failures produce enormous counterexamples that are impossible to debug
tags: shrinking, debugging, counterexample, reproduction, seed
---

# Shrinking and Debugging Failures

When a property fails, the framework shrinks the input to the smallest
counterexample that still triggers the failure. This is the killer feature
of PBT -- it does the debugging work for you.

## How Shrinking Works

1. Test finds a failing input (e.g., a list of 200 integers)
2. Framework tries smaller inputs: remove elements, reduce values
3. After each reduction, re-run the property
4. If it still fails, keep the smaller input. If it passes, discard the reduction
5. Repeat until no further reduction causes failure

The result is the **minimal counterexample** -- the simplest input that
breaks your code.

## Debugging a Shrunk Failure

### Step 1: Read the counterexample

```
Falsifying example: test_sort_preserves_elements(xs=[0, -1])
```

This is the MINIMAL case. The bug is in how your code handles `[0, -1]`,
not in some edge case with 200 elements.

### Step 2: Reproduce with the seed

Every framework provides a seed for reproduction:

```python
# Hypothesis
@settings(database=None)  # disable example DB
@seed(12345)  # from failure output
def test_sort_preserves_elements(xs): ...
```

```bash
# proptest
PROPTEST_SEED=12345 cargo test test_sort_preserves_elements
```

```bash
# StreamData
mix test --seed 12345
```

### Step 3: Write a regression example test

Once you understand the bug, add a fixed example test for the minimal
counterexample. This ensures the bug stays fixed even if someone removes
the property test later.

```python
def test_sort_handles_zero_and_negative():
    """Regression: PBT found that [0, -1] was mishandled."""
    assert my_sort([0, -1]) == [-1, 0]
```

### Step 4: Fix the bug and re-run

After fixing, re-run the property test with a high example count to confirm
the fix covers the general case, not just the shrunk example.

## Common Shrinking Problems

### Problem: Shrinking is slow

```python
# BAD: complex composite generator, shrinking takes minutes
@given(complex_nested_structure())
@settings(deadline=None)  # don't timeout during shrinking
def test_complex(data): ...
```

**Fix:** Decompose the generator. Simpler generators shrink faster.

### Problem: Shrunk example is not minimal

This happens when using `filter()` / `assume()` -- the shrinker tries
reductions that get rejected by the filter, so it gives up early.

**Fix:** Build a generator that produces valid inputs directly instead
of filtering. See `generators.md`.

### Problem: Custom generator doesn't shrink

Hand-rolled generators that return raw values do not shrink:

```python
# BAD: no shrinking
@st.composite
def bad_gen(draw):
    return random.randint(0, 100)  # bypasses Hypothesis, no shrinking

# GOOD: shrinks naturally
@st.composite
def good_gen(draw):
    return draw(st.integers(min_value=0, max_value=100))
```

**Rule:** Always use `draw()` (Hypothesis) or the framework's combinators.
Never call `random` directly.

## CI Configuration

### Fixed seed for determinism

```python
# conftest.py
from hypothesis import settings, Phase
settings.register_profile("ci",
    max_examples=200,
    derandomize=True,
    phases=[Phase.explicit, Phase.generate, Phase.shrink],
)
settings.load_profile("ci")
```

```toml
# proptest.toml (Rust)
[default]
cases = 200
```

### Local exploration (more examples, no seed)

```python
settings.register_profile("dev",
    max_examples=1000,
    derandomize=False,
)
# Run with: HYPOTHESIS_PROFILE=dev pytest
```

### Failure database

Hypothesis stores failing examples in `.hypothesis/`. Commit this directory
so that known failures are re-tested on every run, even with different seeds.

```gitignore
# DO commit
.hypothesis/examples/

# DO NOT commit
.hypothesis/unicode_data/
```
