---
title: Testing Payments + ACP
impact: HIGH
impactDescription: Tests that hit a live bundler or RPC are flaky, slow, and can move real funds.
tags: raxol, payments, acp, testing, mock
---

# Testing Payments + ACP

Never touch a live chain, bundler, or Xochi endpoint in tests. Use the in-process Mock
provider adapter and deterministic wallets.

## Mock provider adapter (ACP)

`Raxol.ACP.ProviderAdapter.Mock` records every call and lets you preset receipts, reads,
and logs -- so you can exercise the full job lifecycle with no RPC.

```elixir
adapter = Raxol.ACP.ProviderAdapter.Mock.new(address: "0x1234..", supported_chain_ids: [8453])
:ok = Raxol.ACP.ProviderAdapter.Mock.set_receipt(adapter, "0xtx", %{status: 1})

{:ok, ["0xtx"]} =
  Raxol.ACP.ProviderAdapter.send_calls(adapter, 8453, [%{to: "0xcore", data: "0x.."}])

# assert what the client actually sent
assert [{8453, [%{to: "0xcore"}]}] = Raxol.ACP.ProviderAdapter.Mock.sent_calls(adapter)
```

Other setters: `set_contract_read/4`, `set_logs/2`, `set_send_calls_error/2`;
inspect signatures with `sent_signatures/1`.

## Ledger + SpendGate

Use a real `Ledger` (it's just ETS) with an in-memory policy; assert `try_spend/5` and
`get_totals/3`. No mocking needed -- the ledger has no external dependency.

```elixir
{:ok, ledger} = Raxol.Payments.Ledger.start_link()
:ok = Raxol.Payments.Ledger.record_spend(ledger, "a", Decimal.new("0.05"), %{})
assert %{session: session} = Raxol.Payments.Ledger.get_totals(ledger, "a", policy)
```

## Nonce serialization

Assert `NonceServer` hands out increasing nonces (the concurrent-send regression):

```elixir
{:ok, _} = Raxol.ACP.Wallet.NonceServer.start_link(name: N, initial_nonce: 12)
assert 12 = Raxol.ACP.Wallet.NonceServer.get_next(N)
assert 13 = Raxol.ACP.Wallet.NonceServer.get_next(N)
```

## Telemetry assertions

Attach to payment events and assert they fire rather than reaching into internals:
`[:raxol, :payments, :spend]`, `[:raxol, :payments, :over_budget]`,
`[:raxol, :payments, :xochi, :settled]`, and the ACP contract event
`[:raxol, :acp, :job_session, :transition]`.

## Pitfalls

1. **Live bundler in tests** -- always the Mock adapter; a real bundler moves funds.
2. **Sleeping to await settlement** -- drive terminal status via the Mock's preset
   receipts, not `Process.sleep`.
3. **Asserting internal state** -- prefer telemetry events + `sent_calls/1` over poking
   GenServer state.
