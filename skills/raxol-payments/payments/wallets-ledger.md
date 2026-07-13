---
title: Wallets, Ledger + Spend Gate
impact: HIGH
impactDescription: Signing without gating budget or without a checkpoint leaks reservations and double-spends on retry.
tags: raxol, payments, wallet, ledger, spend, checkpoint
---

# Wallets, Ledger + Spend Gate

## Wallets (`Raxol.Payments.Wallet`)

Behaviour: `address/0`, `chain_id/0`, `sign_message/1`, `sign_typed_data/3`,
`sign_hash/1`. Pick an implementation per deployment:

```elixir
# EOA from an env var (address derived at load)
defmodule MyWallet do
  use Raxol.Payments.Wallets.Env, env_var: "MY_KEY", chain_id: 8453
end

# EOA from 1Password (GenServer; key never on disk)
{:ok, w} = Raxol.Payments.Wallets.Op.start_link(
  op_ref: "op://Employee/RaxolKey/credential", chain_id: 8453)
addr = Raxol.Payments.Wallets.Op.address(w)
```

For ERC-4337 smart accounts and EOA nonce serialization, see
`acp/job-lifecycle.md` (`Raxol.ACP.Wallet.SCA` / `Wallet.NonceServer`).

## Ledger (spend limits)

`Raxol.Payments.Ledger` is an ETS-backed GenServer tracking spend against a
`SpendingPolicy`, with reservations (TTL + sweep) and a freeze flag.

```elixir
{:ok, ledger} = Raxol.Payments.Ledger.start_link()

:ok = Raxol.Payments.Ledger.record_spend(ledger, "agent1", Decimal.new("0.05"),
        %{domain: "api.example.com", protocol: :xochi, tx_hash: "0x.."})

case Raxol.Payments.Ledger.try_spend(ledger, "agent1", Decimal.new("0.10"), policy, %{}) do
  :ok -> :proceed
  {:over_limit, which} -> {:blocked, which}   # e.g. :per_tx | :session | :lifetime
end

%{session: s, lifetime: l} =
  Raxol.Payments.Ledger.get_totals(ledger, "agent1", policy)
```

Freeze/subscribe for a kill switch + live monitoring: `freeze/1`, `unfreeze/1`,
`frozen?/1`, `subscribe/2`, `tail/2`.

## SpendGate (authorize -> reserve -> release)

`Raxol.Payments.Actions.SpendGate` is the gate every payment passes through. It reserves
budget before you sign and releases it after settlement (or refunds on failure).

```elixir
ctx = %{ledger: ledger, policy: policy, agent_id: "agent1",
        wallet: MyWallet, on_confirm: fn _amt, _domain -> :approve end}

:ok = SpendGate.authorize(ctx, Decimal.new("0.05"),
        target: {:domain, "api.xochi.fi"}, metadata: %{protocol: :xochi})

# tag the reservation to an intent so you can release exactly it later
:ok = SpendGate.tag_reservation(ctx, intent_id, Decimal.new("0.05"))

# on terminal status:
SpendGate.release_by_intent(ctx, intent_id)   # :released | :noop
```

## Mandates (delegated auth)

`Raxol.Payments.Req.Mandate.attach/2` adds a mandate delegation header
(`X-Xochi-Delegation`) to outbound `Req` calls for hosts/paths the agent is authorized
for. `Req.AutoPay` and `Req.AgentPlugin` layer 402 auto-pay and agent identity onto a
`Req` pipeline.

## Checkpoints (idempotency)

`Raxol.Payments.Checkpoint` is a pluggable store (`ETS` / `ContextStore`) for in-flight
intent records. Derive a stable key from canonical fields and short-circuit retries.

```elixir
store = {Raxol.Payments.Checkpoint.ETS, cp}
key   = Raxol.Payments.Checkpoint.derive_key([from_chain, to_chain, amount, nonce])

case Raxol.Payments.Checkpoint.fetch(store, key) do
  {:ok, rec} -> {:already_submitted, rec}
  :error ->
    :ok = Raxol.Payments.Checkpoint.put(store, key, %{intent_id: id})
    submit()
end
```

## Directive.Pay

`Raxol.Payments.Directive.Pay.new(amount:, domain:, perform:, ...)` is a semantic
payment effect for TEA agents; on completion it delivers `:pay_result` / `:pay_error`.

## Pitfalls

1. **Reservation leak** -- always pair `authorize` with `release`/`release_by_intent`;
   otherwise a failed send holds budget until the TTL sweep.
2. **Float amounts** -- `Decimal` only; the ledger sums decimals.
3. **No checkpoint on retry** -- `derive_key` + `fetch` before re-submitting or you
   double-spend.
