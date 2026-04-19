---
title: Refactoring Patterns
impact: HIGH
impactDescription: Using the wrong refactoring pattern increases risk and creates unnecessary intermediate states
tags: extract, inline, move, rename, patterns, polyglot
---

# Refactoring Patterns

Mechanical transformations that change structure without changing behavior.
Each pattern is a single commit. Apply one at a time, run tests after each.

## Extract (most common)

Pull code out of a large unit into a smaller, named unit.

### Extract Function

**Signal:** A block of code inside a function does one identifiable thing.

```python
# Before
def process_order(order):
    # validate
    if not order.items:
        raise ValueError("empty order")
    if order.total < 0:
        raise ValueError("negative total")
    # ... 50 more lines of processing

# After: extract validation
def _validate_order(order):
    if not order.items:
        raise ValueError("empty order")
    if order.total < 0:
        raise ValueError("negative total")

def process_order(order):
    _validate_order(order)
    # ... 50 lines of processing (unchanged)
```

### Extract Module / Class

**Signal:** A file has 500+ lines with two or more unrelated responsibilities.

```elixir
# Before: one large module
defmodule App.Orders do
  def create(params), do: ...
  def validate(order), do: ...
  def calculate_tax(order), do: ...
  def format_receipt(order), do: ...
  def send_confirmation(order), do: ...
end

# After: extract tax and receipt concerns
defmodule App.Orders do
  def create(params), do: ...
  def validate(order), do: ...
end

defmodule App.Orders.Tax do
  def calculate(order), do: ...
end

defmodule App.Orders.Receipt do
  def format(order), do: ...
  def send_confirmation(order), do: ...
end
```

### Extract Interface / Behaviour

**Signal:** Multiple implementations exist (or will exist) for the same contract.

```elixir
# Extract a behaviour
defmodule App.Notifier do
  @callback send(recipient :: String.t(), message :: String.t()) :: :ok | {:error, term()}
end

defmodule App.Notifier.Email do
  @behaviour App.Notifier
  def send(recipient, message), do: ...
end
```

```go
// Extract an interface
type Notifier interface {
    Send(recipient, message string) error
}

type EmailNotifier struct{}
func (n *EmailNotifier) Send(recipient, message string) error { ... }
```

## Inline (reverse of Extract)

Collapse an unnecessary abstraction back into its caller.

**Signal:** A function/module/class that is called from exactly one place and
adds no clarity. The abstraction is shallower than the code it wraps.

```typescript
// Before: unnecessary wrapper
function getUserName(user: User): string {
  return user.name;
}
// ... only caller:
const name = getUserName(user);

// After: inline
const name = user.name;
```

**When NOT to inline:** If the abstraction enforces a constraint, documents
intent, or is called from multiple places.

## Move

Relocate code to where it belongs.

### Move Function

**Signal:** Feature envy -- a function uses more data from another module than
from its own.

```rust
// Before: Order module envies Customer data
impl Order {
    fn shipping_label(&self) -> String {
        format!("{}\n{}\n{}, {}",
            self.customer.name,
            self.customer.street,
            self.customer.city,
            self.customer.state)
    }
}

// After: Customer owns its formatting
impl Customer {
    fn address_label(&self) -> String {
        format!("{}\n{}\n{}, {}", self.name, self.street, self.city, self.state)
    }
}
```

### Move File / Module

**Signal:** A file is in the wrong directory for its responsibility. Tests
import it with a path that does not match its concern.

**Execution:**
1. Create the new file in the correct location
2. Update all imports (use language-aware rename tools when available)
3. Run the full test suite
4. Delete the old file
5. Commit

## Rename

Change names to reveal intent. The most underrated refactoring.

### Single-file rename

Safe with any editor's rename refactoring. One commit.

### Cross-codebase rename

Dangerous without tooling. Use language-aware rename:

| Language | Tool | Command |
|----------|------|---------|
| TypeScript | ts-morph or IDE | Rename symbol |
| Rust | rust-analyzer | `ra rename` |
| Python | rope or IDE | Rename symbol |
| Elixir | elixir_sense or manual | grep + replace |
| Go | gorename | `gorename -from "pkg.OldName" -to NewName` |

**For languages without refactoring tools (Elixir, Lua):**

1. Grep for all occurrences: `rg "OldName" --type elixir`
2. Replace with confirmed list: `rg "OldName" -l | xargs sed -i 's/OldName/NewName/g'`
3. Run the full test suite
4. Review the diff manually -- sed may have renamed things in comments or
   strings that should not change

## Pattern Selection

```
Code is too long --> Extract function/module
Abstraction adds no value --> Inline
Code is in the wrong place --> Move
Name doesn't reveal intent --> Rename
```

Start with the simplest pattern that addresses the smell. Compound
refactorings (extract + move + rename) should be separate commits.
