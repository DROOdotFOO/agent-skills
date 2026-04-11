---
title: Mocking Strategy
impact: CRITICAL
impactDescription: Wrong mocking couples tests to implementation, making every refactor break the suite
tags: mocking, dependency-injection, test-doubles, boundaries
---

# Mocking Strategy

**Default rule: no mocks in tests unless explicitly requested.**

Mock only at **system boundaries** -- the seams where your code meets infrastructure you do not control.

## When to Mock

| Boundary | Example | Why |
|----------|---------|-----|
| External APIs | HTTP calls to Stripe, GitHub | Slow, flaky, costs money |
| Databases | PostgreSQL, Redis | Prefer real test DB; mock only when impractical |
| Time | `DateTime.now()`, `time.time()` | Non-determinism breaks assertions |
| Randomness | `random.random()`, `Enum.random/1` | Non-determinism |
| Filesystem | Reading config files, temp dirs | Environment-dependent |

## When NOT to Mock

- Your own modules, functions, or classes
- Internal utilities (normalization, validation, formatting)
- Anything you could test by calling the real code

If you feel the urge to mock an internal module, the design is wrong. Inject the dependency instead.

## DI Patterns by Language

### Python

```python
# Accept the dependency, don't create it
class OrderService:
    def __init__(self, payment_gateway: PaymentGateway) -> None:
        self._gateway = payment_gateway

    def place_order(self, order: Order) -> Receipt:
        charge = self._gateway.charge(order.total)
        return Receipt(order_id=order.id, charge_id=charge.id)

# In tests: inject a fake gateway (system boundary)
class FakePaymentGateway:
    def charge(self, amount: int) -> Charge:
        return Charge(id="fake-charge", amount=amount)

def test_place_order():
    svc = OrderService(FakePaymentGateway())
    receipt = svc.place_order(Order(id="1", total=1000))
    assert receipt.charge_id == "fake-charge"
```

### Elixir

```elixir
# Use behaviours for boundary contracts
defmodule MyApp.PaymentGateway do
  @callback charge(amount :: integer()) :: {:ok, String.t()} | {:error, term()}
end

defmodule MyApp.OrderService do
  def place_order(order, gateway \\ MyApp.StripeGateway) do
    with {:ok, charge_id} <- gateway.charge(order.total) do
      {:ok, %Receipt{order_id: order.id, charge_id: charge_id}}
    end
  end
end

# In tests: use a fake module (not Mox unless at a real boundary)
defmodule FakeGateway do
  @behaviour MyApp.PaymentGateway
  def charge(_amount), do: {:ok, "fake-charge"}
end

test "place_order returns receipt" do
  {:ok, receipt} = MyApp.OrderService.place_order(order, FakeGateway)
  assert receipt.charge_id == "fake-charge"
end
```

### Go

```go
// Accept interfaces, return structs
type PaymentGateway interface {
    Charge(amount int) (string, error)
}

type OrderService struct {
    gateway PaymentGateway
}

func NewOrderService(gw PaymentGateway) *OrderService {
    return &OrderService{gateway: gw}
}

// In tests: implement the interface
type fakeGateway struct{}

func (f *fakeGateway) Charge(amount int) (string, error) {
    return "fake-charge", nil
}

func TestPlaceOrder(t *testing.T) {
    svc := NewOrderService(&fakeGateway{})
    receipt, err := svc.PlaceOrder(order)
    require.NoError(t, err)
    assert.Equal(t, "fake-charge", receipt.ChargeID)
}
```

### Rust

```rust
// Use traits for boundary abstraction
trait PaymentGateway {
    fn charge(&self, amount: u64) -> Result<String, PaymentError>;
}

struct OrderService<G: PaymentGateway> {
    gateway: G,
}

impl<G: PaymentGateway> OrderService<G> {
    fn place_order(&self, order: &Order) -> Result<Receipt, PaymentError> {
        let charge_id = self.gateway.charge(order.total)?;
        Ok(Receipt { order_id: order.id.clone(), charge_id })
    }
}

// In tests
struct FakeGateway;
impl PaymentGateway for FakeGateway {
    fn charge(&self, _amount: u64) -> Result<String, PaymentError> {
        Ok("fake-charge".into())
    }
}

#[test]
fn place_order_returns_receipt() {
    let svc = OrderService { gateway: FakeGateway };
    let receipt = svc.place_order(&test_order()).unwrap();
    assert_eq!(receipt.charge_id, "fake-charge");
}
```

### TypeScript

```typescript
// Accept the dependency via constructor
interface PaymentGateway {
  charge(amount: number): Promise<string>;
}

class OrderService {
  constructor(private gateway: PaymentGateway) {}

  async placeOrder(order: Order): Promise<Receipt> {
    const chargeId = await this.gateway.charge(order.total);
    return { orderId: order.id, chargeId };
  }
}

// In tests: pass a fake (only for external boundary)
const fakeGateway: PaymentGateway = {
  charge: async () => "fake-charge",
};

test("placeOrder returns receipt", async () => {
  const svc = new OrderService(fakeGateway);
  const receipt = await svc.placeOrder(testOrder);
  expect(receipt.chargeId).toBe("fake-charge");
});
```
