---
title: Custom Generators
impact: HIGH
impactDescription: Bad generators produce invalid inputs that waste test budget on assume() rejections or miss the interesting parts of the domain
tags: generators, strategies, composition, domain, filtering
---

# Custom Generators

Built-in generators (integers, strings, lists) are a starting point. Real
code has constrained domains: valid emails, balanced trees, non-empty sorted
lists. Custom generators produce valid inputs directly instead of filtering.

## Principle: Generate, Don't Filter

```python
# BAD: generates random strings, rejects 99%+ as invalid emails
@given(st.text())
def test_email(s):
    assume("@" in s and "." in s.split("@")[1])  # almost never true
    process_email(s)

# GOOD: generates valid emails directly
email_strategy = st.builds(
    lambda user, domain, tld: f"{user}@{domain}.{tld}",
    st.from_regex(r"[a-z][a-z0-9]{1,20}", fullmatch=True),
    st.from_regex(r"[a-z]{2,10}", fullmatch=True),
    st.sampled_from(["com", "org", "net", "io"]),
)
```

If `assume()` rejects more than 10% of generated inputs, build a custom
generator instead.

## Composition Patterns

### Map (transform a generator)

```python
# Python: positive even integers
even_ints = st.integers(min_value=1).map(lambda x: x * 2)
```

```rust
// Rust: non-empty strings
prop::string::string_regex("[a-z]{1,50}").unwrap()
```

```elixir
# Elixir: positive even integers
gen = StreamData.positive_integer() |> StreamData.map(&(&1 * 2))
```

### Bind (dependent generators)

Generate one value, then use it to constrain the next.

```python
# List and a valid index into it
@st.composite
def list_with_index(draw):
    xs = draw(st.lists(st.integers(), min_size=1))
    i = draw(st.integers(min_value=0, max_value=len(xs) - 1))
    return xs, i
```

```elixir
gen =
  StreamData.bind(StreamData.list_of(StreamData.integer(), min_length: 1), fn xs ->
    StreamData.bind(StreamData.integer(0..(length(xs) - 1)), fn i ->
      StreamData.constant({xs, i})
    end)
  end)
```

### One-of (union of generators)

```python
json_value = st.recursive(
    st.none() | st.booleans() | st.integers() | st.text(),
    lambda children: st.lists(children) | st.dictionaries(st.text(), children),
)
```

```rust
prop_oneof![
    Just(Value::Null),
    any::<bool>().prop_map(Value::Bool),
    any::<i64>().prop_map(Value::Int),
    "[a-z]{0,20}".prop_map(Value::Str),
]
```

### Recursive (trees, nested structures)

```python
# Binary trees
@st.composite
def trees(draw, max_depth=5):
    if max_depth == 0 or draw(st.booleans()):
        return Leaf(draw(st.integers()))
    left = draw(trees(max_depth=max_depth - 1))
    right = draw(trees(max_depth=max_depth - 1))
    return Node(left, right)
```

## Domain-Specific Generator Patterns

### Constrained numeric ranges

```python
# Valid percentage (0.0 to 100.0, max 2 decimal places)
pct = st.floats(min_value=0, max_value=100).map(lambda x: round(x, 2))
```

### Valid identifiers

```python
identifier = st.from_regex(r"[a-z_][a-z0-9_]{0,30}", fullmatch=True)
```

### Sorted lists

```python
sorted_list = st.lists(st.integers()).map(sorted)
```

### Non-overlapping intervals

```python
@st.composite
def intervals(draw):
    points = sorted(draw(st.lists(st.integers(), min_size=4, max_size=20, unique=True)))
    return [(points[i], points[i + 1]) for i in range(0, len(points) - 1, 2)]
```

## Testing the Generator

Before using a custom generator in property tests, verify it produces the
inputs you expect:

```python
# Hypothesis: print samples
email_strategy.example()  # call multiple times to inspect

# Or in a test:
@given(email_strategy)
def test_generator_sanity(email):
    assert "@" in email
    assert "." in email.split("@")[1]
```

```elixir
# StreamData: inspect samples
Enum.take(StreamData.list_of(StreamData.integer()), 5)
```

## Shrinking Compatibility

Custom generators must shrink well. Prefer composition (map, bind, one_of)
over raw generation -- composed generators inherit shrinking from their
components. Hand-rolled generators that return raw values will not shrink,
making failures harder to debug. See `shrinking.md`.
