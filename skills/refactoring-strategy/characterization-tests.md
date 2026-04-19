---
title: Characterization Tests
impact: CRITICAL
impactDescription: Refactoring without characterization tests means you cannot distinguish intentional behavior changes from regressions
tags: characterization-tests, pinning, golden-master, approval, safety
---

# Characterization Tests

Characterization tests (also called "pinning tests" or "golden master tests")
document what code does NOW, not what it SHOULD do. They are a safety net for
refactoring -- if a characterization test fails after a refactoring commit,
you changed behavior, not just structure.

## When to Write Them

**Before every refactoring session.** Not after. Not "as you go." Before.

Write characterization tests when:
- The code has no tests or inadequate tests
- You do not fully understand all code paths
- The code has implicit behavior that callers depend on (error messages, side effects, ordering)
- You plan to change the internal structure of a module

## How to Write Them

### Step 1: Identify the public interface

Find every function, method, endpoint, or command that external code calls.
These are the boundaries you must pin.

### Step 2: Call with real inputs, assert real outputs

Do NOT write tests for what the code SHOULD do. Write tests for what it
ACTUALLY does, including bugs.

```python
def test_parse_header_characterization():
    """Pins current behavior. The trailing space IS the current behavior."""
    result = parse_header("Content-Type: text/html ")
    # Note: includes trailing space -- may be a bug, but callers may depend on it
    assert result == {"Content-Type": "text/html "}
```

```elixir
test "parse_header preserves trailing whitespace" do
  # Characterization: this IS the current behavior, bug or not
  assert parse_header("Content-Type: text/html ") ==
           %{"Content-Type" => "text/html "}
end
```

### Step 3: Cover edge cases you discover

As you read the code, you will find branches and conditions. Write a
characterization test for each path, especially:

- Error cases (what exception? what message?)
- Empty inputs
- Nil/null handling
- Boundary values
- Side effects (files written, logs emitted, metrics recorded)

### Step 4: Run and verify

Run the tests. They must all pass against the CURRENT code. If any fail,
your test is wrong -- fix the assertion to match actual behavior.

## Golden Master Pattern

For functions with complex output (HTML rendering, report generation,
serialization), use golden master (snapshot) testing:

```python
def test_report_golden_master():
    report = generate_report(sample_data)
    golden = Path("tests/golden/report.txt").read_text()
    assert report == golden

# First run: create the golden file
# Path("tests/golden/report.txt").write_text(generate_report(sample_data))
```

```rust
#[test]
fn report_golden_master() {
    let report = generate_report(&sample_data());
    insta::assert_snapshot!(report);  // insta crate manages golden files
}
```

```elixir
# Use assert_value or manual snapshot
test "report golden master" do
  report = generate_report(sample_data())
  expected = File.read!("test/golden/report.txt")
  assert report == expected
end
```

**Tooling:** Rust has `insta`, Python has `syrupy`, Elixir has `assert_value`.
These manage golden files and provide diff-based review on changes.

## Characterization Test Lifecycle

```
1. WRITE characterization tests (pin current behavior)
2. VERIFY they pass against current code
3. REFACTOR the code (structure only, not behavior)
4. RE-RUN characterization tests -- they must still pass
5. REMOVE redundant characterization tests after refactoring
   (replace with proper unit tests for the new structure)
```

**Do not keep characterization tests forever.** They are scaffolding. Once
the refactoring is complete and proper tests exist for the new structure,
remove the characterization tests. They document the old structure, which no
longer exists.

## Common Pitfalls

| Mistake | Fix |
|---------|-----|
| Writing aspirational tests instead of characterization tests | Assert what the code DOES, not what you want it to do |
| Forgetting to pin error messages and side effects | Test the full observable behavior, not just return values |
| Keeping characterization tests after refactoring is done | Replace with proper unit tests for the new structure |
| Testing internal methods instead of public interface | Pin at the boundary that external code uses |
| Not running characterization tests before refactoring | They must pass against the CURRENT code first |
