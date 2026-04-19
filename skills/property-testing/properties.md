---
title: Property Taxonomy
impact: CRITICAL
impactDescription: Choosing the wrong property type produces tests that either restate the implementation or test nothing useful
tags: properties, roundtrip, invariant, oracle, metamorphic, model-based
---

# Property Taxonomy

Five categories of properties, from most to least common. Start with roundtrip
and invariant -- they cover 80% of real-world PBT use cases.

## 1. Roundtrip (Encode/Decode)

Apply a transformation and its inverse. The result must equal the original.

```
decode(encode(x)) == x
```

**When to use:** Serialization, parsing, compression, encryption, any codec.

```python
# Python
@given(st.dictionaries(st.text(), st.integers()))
def test_json_roundtrip(d):
    assert json.loads(json.dumps(d)) == d
```

```rust
// Rust
proptest! {
    #[test]
    fn cbor_roundtrip(msg: Message) {
        let bytes = serde_cbor::to_vec(&msg).unwrap();
        let decoded: Message = serde_cbor::from_slice(&bytes).unwrap();
        prop_assert_eq!(decoded, msg);
    }
}
```

```elixir
# Elixir
property "JSON roundtrip" do
  check all map <- map_of(string(:alphanumeric), integer()) do
    assert map |> Jason.encode!() |> Jason.decode!() == map
  end
end
```

**Gotcha:** Roundtrip may fail on lossy transformations (e.g., float -> string
loses precision). Either restrict the input domain or test approximate equality.

## 2. Invariant (Preserved Property)

A property that must hold before and after a transformation.

```
len(sort(xs)) == len(xs)
set(sort(xs)) == set(xs)
```

**When to use:** Sorting, filtering, mapping, any collection transformation.

```python
@given(st.lists(st.integers()))
def test_sort_preserves_elements(xs):
    sorted_xs = sorted(xs)
    assert len(sorted_xs) == len(xs)
    assert set(sorted_xs) == set(xs)
    # bonus: sorted output is actually sorted
    assert all(a <= b for a, b in zip(sorted_xs, sorted_xs[1:]))
```

```elixir
property "filter preserves membership" do
  check all xs <- list_of(integer()), pred = fn x -> rem(x, 2) == 0 end do
    filtered = Enum.filter(xs, pred)
    assert Enum.all?(filtered, pred)
    assert length(filtered) <= length(xs)
  end
end
```

**Common invariants:** length preservation, element preservation, ordering,
uniqueness, range bounds, type preservation.

## 3. Oracle (Reference Implementation)

Compare the implementation under test against a known-correct reference.

```
fast_sort(xs) == stdlib_sort(xs)
```

**When to use:** Optimized implementations, reimplementations, ports between
languages. The reference can be slow -- it only runs in tests.

```python
@given(st.lists(st.integers()))
def test_custom_sort_matches_stdlib(xs):
    assert my_quicksort(xs) == sorted(xs)
```

```rust
proptest! {
    #[test]
    fn optimized_hash_matches_reference(data: Vec<u8>) {
        prop_assert_eq!(fast_hash(&data), reference_hash(&data));
    }
}
```

**Gotcha:** If the reference IS the implementation, you are testing nothing.
The reference must be independently derived (stdlib, textbook algorithm,
previous version).

## 4. Metamorphic (Input Relationship)

When you cannot state the output directly, state a relationship between
outputs for related inputs.

```
If f(x) = y, then f(x + 1) >= y  (for monotonic functions)
```

**When to use:** Functions with complex outputs where you cannot state the
exact answer, but you know how changes in input should affect the output.
ML models, search ranking, pricing algorithms.

```python
@given(st.floats(min_value=0, max_value=1e6))
def test_tax_is_monotonic(income):
    assume(income > 0)
    assert calculate_tax(income * 1.1) >= calculate_tax(income)
```

```elixir
property "search results are monotonic in relevance" do
  check all query <- string(:alphanumeric, min_length: 1),
            extra <- string(:alphanumeric, min_length: 1) do
    short_results = search(query)
    long_results = search(query <> " " <> extra)
    # more specific query should return fewer or equal results
    assert length(long_results) <= length(short_results)
  end
end
```

**Key insight:** Metamorphic testing is often the only option for testing
"black box" systems where the expected output is hard to compute.

## 5. Model-Based (State Machine)

Model the system as a state machine. Generate sequences of operations.
Assert that the real system's state matches the model after each step.

**When to use:** Stateful systems (databases, caches, queues, protocols),
concurrent data structures, file systems.

```python
# Hypothesis stateful testing
class QueueModel(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()
        self.model = []          # simple list as reference
        self.real = MyQueue()    # system under test

    @rule(x=st.integers())
    def push(self, x):
        self.model.append(x)
        self.real.push(x)

    @precondition(lambda self: len(self.model) > 0)
    @rule()
    def pop(self):
        expected = self.model.pop(0)
        actual = self.real.pop()
        assert actual == expected

    @rule()
    def check_size(self):
        assert len(self.model) == self.real.size()

TestQueue = QueueModel.TestCase
```

```elixir
# StreamData + ExUnitProperties
property "stack model" do
  check all cmds <- list_of(one_of([
    constant(:push), constant(:pop), constant(:peek)
  ])) do
    {model, real} = Enum.reduce(cmds, {[], Stack.new()}, fn
      :push, {m, r} -> {[1 | m], Stack.push(r, 1)}
      :pop, {[_ | m], r} -> {m, Stack.pop(r) |> elem(1)}
      :pop, {[], r} -> {[], r}  # no-op on empty
      :peek, {m, r} ->
        assert Stack.peek(r) == List.first(m)
        {m, r}
    end)
    assert length(model) == Stack.size(real)
  end
end
```

**This is the most powerful property type** but also the most complex.
Start with roundtrip/invariant and reach for model-based testing when
the system is inherently stateful.

## Choosing a Property Type

```
Can you reverse the operation?
  Yes --> Roundtrip
  No  --> Is there a known-correct reference?
    Yes --> Oracle
    No  --> Can you state what should be preserved?
      Yes --> Invariant
      No  --> Can you relate outputs for related inputs?
        Yes --> Metamorphic
        No  --> Is the system stateful?
          Yes --> Model-based
          No  --> Example tests may be sufficient for this case
```
