---
title: Post-TDD Refactoring
impact: HIGH
impactDescription: Refactoring while GREEN preserves behavior guarantees; refactoring without tests is guessing
tags: refactoring, code-smells, clean-code, tdd
---

# Post-TDD Refactoring

Refactor ONLY when all tests are GREEN. After each refactor step, run the full suite. If anything goes RED, revert the last change and try a smaller step.

## Refactor Candidates

### 1. Duplication

Two or more places doing the same thing. Extract a function, module, or shared constant.

**Signal:** You copy-pasted code and changed one or two values.

```python
# Before: duplicated validation
def create_user(email: str) -> User:
    if not email or "@" not in email:
        raise ValueError("invalid email")
    # ...

def update_email(user: User, email: str) -> User:
    if not email or "@" not in email:
        raise ValueError("invalid email")
    # ...

# After: extracted
def _validate_email(email: str) -> None:
    if not email or "@" not in email:
        raise ValueError("invalid email")
```

### 2. Long Methods

A function doing too many things. Split into smaller functions with descriptive names.

**Signal:** You need comments to separate "sections" within a function, or the function scrolls off screen.

### 3. Shallow Modules

A module whose interface is as complex as its implementation. Combine with related modules or deepen the abstraction (see [deep-modules.md](deep-modules.md)).

**Signal:** Callers must understand internals to use the module correctly.

### 4. Feature Envy

A function that uses more data from another module than from its own. Move the function to where the data lives.

**Signal:** Lots of `other_module.field` accesses.

```elixir
# Before: Order module envies User data
def shipping_label(order) do
  "#{order.user.name}\n#{order.user.street}\n#{order.user.city}, #{order.user.state}"
end

# After: User owns its own formatting
defmodule User do
  def address_label(user) do
    "#{user.name}\n#{user.street}\n#{user.city}, #{user.state}"
  end
end
```

### 5. Primitive Obsession

Using raw strings, integers, or maps where a dedicated type would add clarity and safety.

**Signal:** Multiple functions pass around the same group of primitives, or you validate the same string format in multiple places.

```rust
// Before: email is just a String everywhere
fn send_email(to: String, subject: String, body: String) { /* ... */ }

// After: newtype with validation
struct Email(String);

impl Email {
    fn parse(raw: &str) -> Result<Self, EmailError> {
        if raw.contains('@') {
            Ok(Email(raw.to_lowercase()))
        } else {
            Err(EmailError::Invalid)
        }
    }
}

fn send_email(to: Email, subject: &str, body: &str) { /* ... */ }
```

### 6. Unclear Names

A variable, function, or module name that requires you to read the implementation to understand its purpose. Rename to reveal intent.

**Signal:** Single-letter variables outside of loops, abbreviations that are not universally understood, generic names like `data`, `result`, `handle`, `process`.

## Refactoring Workflow

1. Confirm all tests are GREEN
2. Identify ONE smell from the list above
3. Make the smallest change that addresses it
4. Run the full test suite
5. If GREEN, commit (or continue to the next smell)
6. If RED, revert and try a smaller step

Never combine refactoring with adding new behavior. Refactoring changes structure without changing behavior. New behavior requires a new RED test first.
