---
title: Interface Design for Testability
impact: HIGH
impactDescription: Interface shape determines whether tests are simple and stable or brittle and complex
tags: design, interfaces, dependency-injection, testability
---

# Interface Design for Testability

Three principles that make code naturally testable without contortions.

## 1. Accept Dependencies, Don't Create Them

A function that creates its own dependencies is hard to test because you cannot substitute them.

### WRONG

```python
class ReportGenerator:
    def generate(self, user_id: int) -> str:
        db = PostgresConnection("prod-host:5432")  # creates its own dependency
        user = db.query("SELECT * FROM users WHERE id = %s", user_id)
        return f"Report for {user.name}"
```

### CORRECT

```python
class ReportGenerator:
    def __init__(self, db: Database) -> None:
        self._db = db  # accepts dependency

    def generate(self, user_id: int) -> str:
        user = self._db.get_user(user_id)
        return f"Report for {user.name}"
```

This applies in every language. In Go: accept interfaces in constructors. In Elixir: pass module or function as argument. In Rust: use generics bounded by traits.

## 2. Return Results Instead of Side Effects

Functions that return values are trivially testable: call them, check the return. Functions that perform side effects (write to disk, send email, mutate global state) require setup and verification of those side effects.

### WRONG

```go
func ProcessOrder(order Order) {
    // Side effects buried inside
    db.Save(order)
    emailer.Send(order.UserEmail, "Order confirmed")
    metrics.Increment("orders.processed")
}
```

### CORRECT

```go
type OrderResult struct {
    SavedOrder  Order
    Email       Email
    MetricName  string
}

func ProcessOrder(order Order) OrderResult {
    return OrderResult{
        SavedOrder: order.WithStatus("confirmed"),
        Email:      Email{To: order.UserEmail, Subject: "Order confirmed"},
        MetricName: "orders.processed",
    }
}
// Caller decides when/how to execute side effects
```

When side effects are necessary, push them to the edges. The core logic returns data; a thin outer layer executes effects.

## 3. Small Surface Area

Every public function, method, or field is part of the contract you must test and maintain. Minimize the public surface.

**Heuristics:**

- If a method is only used internally, make it private
- If a struct field is only read by the module itself, don't export it
- If a parameter has a sensible default, use the default (functional options in Go, keyword args in Elixir/Python, builder pattern in Rust)
- Prefer one method that handles variations over multiple methods with overlapping behavior

### Go: functional options

```go
type Server struct {
    port    int
    timeout time.Duration
}

type Option func(*Server)

func WithPort(p int) Option    { return func(s *Server) { s.port = p } }
func WithTimeout(d time.Duration) Option { return func(s *Server) { s.timeout = d } }

func NewServer(opts ...Option) *Server {
    s := &Server{port: 8080, timeout: 30 * time.Second}
    for _, o := range opts {
        o(s)
    }
    return s
}
```

### Elixir: keyword defaults

```elixir
def start_link(opts \\ []) do
  port = Keyword.get(opts, :port, 8080)
  timeout = Keyword.get(opts, :timeout, 30_000)
  GenServer.start_link(__MODULE__, %{port: port, timeout: timeout})
end
```

Small surface area means fewer tests, fewer breaking changes, and easier reasoning about behavior.
