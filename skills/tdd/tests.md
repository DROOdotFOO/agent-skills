---
title: Good vs Bad Test Patterns
impact: CRITICAL
impactDescription: Wrong test patterns create brittle suites that resist refactoring and give false confidence
tags: testing, patterns, polyglot, behavior, public-api
---

# Good vs Bad Test Patterns

The core rule: test **behavior through public interfaces**. If you refactor internals and tests break, the tests were wrong.

## Python (pytest)

### WRONG -- testing internal helper

```python
# WRONG: testing private method directly
def test_parse_header():
    parser = MessageParser()
    result = parser._parse_header("Content-Type: text/html")
    assert result == {"Content-Type": "text/html"}
```

### CORRECT -- testing behavior through public API

```python
# CORRECT: test the behavior the caller cares about
def test_parse_extracts_content_type():
    parser = MessageParser()
    msg = parser.parse("Content-Type: text/html\r\n\r\nHello")
    assert msg.content_type == "text/html"
```

### Fixtures and parametrize

```python
import pytest

@pytest.fixture
def sample_message() -> str:
    return "Content-Type: text/html\r\n\r\n<h1>Hello</h1>"

def test_parse_html_message(sample_message: str):
    msg = MessageParser().parse(sample_message)
    assert msg.body == "<h1>Hello</h1>"

@pytest.mark.parametrize("input_,expected", [
    ("", None),
    ("Content-Type: text/plain\r\n\r\nhi", "text/plain"),
    ("Content-Type: application/json\r\n\r\n{}", "application/json"),
])
def test_content_type_extraction(input_: str, expected: str | None):
    msg = MessageParser().parse(input_)
    assert msg.content_type == expected
```

---

## Elixir (ExUnit)

### WRONG -- reaching into internal state

```elixir
# WRONG: inspecting GenServer state directly
test "adds item to internal list" do
  {:ok, pid} = Cart.start_link()
  Cart.add_item(pid, "apple")
  state = :sys.get_state(pid)
  assert "apple" in state.items
end
```

### CORRECT -- testing through public API

```elixir
# CORRECT: test observable behavior
describe "Cart.add_item/2" do
  setup do
    {:ok, pid} = Cart.start_link()
    %{cart: pid}
  end

  test "added item appears in listing", %{cart: cart} do
    Cart.add_item(cart, "apple")
    assert "apple" in Cart.list_items(cart)
  end

  test "adding duplicate increments quantity", %{cart: cart} do
    Cart.add_item(cart, "apple")
    Cart.add_item(cart, "apple")
    assert Cart.item_count(cart, "apple") == 2
  end
end
```

### Doctests

```elixir
defmodule Formatter do
  @doc """
  Formats a price in cents as a dollar string.

      iex> Formatter.format_price(1299)
      "$12.99"

      iex> Formatter.format_price(0)
      "$0.00"
  """
  def format_price(cents) when is_integer(cents) do
    "$#{div(cents, 100)}.#{String.pad_leading("#{rem(cents, 100)}", 2, "0")}"
  end
end
```

---

## Go (table-driven tests)

### WRONG -- testing unexported helper

```go
// WRONG: testing unexported function directly
func Test_normalizeEmail(t *testing.T) {
    got := normalizeEmail("FOO@BAR.com")
    assert.Equal(t, "foo@bar.com", got)
}
```

### CORRECT -- table-driven test on exported API

```go
func TestCreateUser(t *testing.T) {
    tests := []struct {
        name    string
        email   string
        wantErr bool
    }{
        {"valid email", "user@example.com", false},
        {"uppercase normalized", "USER@EXAMPLE.COM", false},
        {"empty email", "", true},
        {"missing domain", "user@", true},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            svc := NewUserService(newTestDB(t))
            user, err := svc.Create(tt.email)
            if tt.wantErr {
                require.Error(t, err)
                return
            }
            require.NoError(t, err)
            assert.Equal(t, strings.ToLower(tt.email), user.Email)
        })
    }
}
```

---

## Rust

### WRONG -- testing private fn with pub(crate) escape hatch

```rust
// WRONG: exposing internals just for testing
pub(crate) fn validate_checksum(data: &[u8]) -> bool { /* ... */ }

#[test]
fn test_validate_checksum() {
    assert!(validate_checksum(b"valid"));
}
```

### CORRECT -- testing through public API

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn decode_valid_message() {
        let msg = Message::decode(b"valid-payload").unwrap();
        assert_eq!(msg.body(), "valid-payload");
    }

    #[test]
    #[should_panic(expected = "invalid checksum")]
    fn decode_rejects_corrupted_data() {
        Message::decode(b"corrupted").unwrap();
    }
}
```

### Property testing with proptest

```rust
use proptest::prelude::*;

proptest! {
    #[test]
    fn roundtrip_encode_decode(input in "\\PC{1,256}") {
        let encoded = Message::encode(input.as_bytes());
        let decoded = Message::decode(&encoded).unwrap();
        prop_assert_eq!(decoded.body(), input);
    }
}
```

---

## TypeScript (Jest / Vitest)

### WRONG -- mocking internal module

```typescript
// WRONG: mocking your own utility to test the service
jest.mock("../utils/normalize", () => ({
  normalizeEmail: (e: string) => e.toLowerCase(),
}));

test("creates user", async () => {
  const user = await createUser("FOO@BAR.COM");
  expect(user.email).toBe("foo@bar.com");
});
```

### CORRECT -- testing observable behavior

```typescript
import { UserService } from "./user-service";
import { createTestDB } from "../test-helpers";

describe("UserService.create", () => {
  it("normalizes email to lowercase", async () => {
    const db = createTestDB();
    const svc = new UserService(db);
    const user = await svc.create("FOO@BAR.COM");
    expect(user.email).toBe("foo@bar.com");
  });

  it("rejects empty email", async () => {
    const db = createTestDB();
    const svc = new UserService(db);
    await expect(svc.create("")).rejects.toThrow("email required");
  });
});
```
