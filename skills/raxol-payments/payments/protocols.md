---
title: Payment Protocols
impact: HIGH
impactDescription: Choosing the wrong protocol or skipping status polling leaves cross-chain intents stuck or double-paid.
tags: raxol, payments, xochi, x402, permit2, protocol
---

# Payment Protocols

All 402-style protocols share `Raxol.Payments.Protocol`:

```elixir
detect?(status, headers) :: boolean()
parse_challenge(headers) :: {:ok, map()} | {:error, term()}
build_payment(challenge, wallet) :: {:ok, headers} | {:error, term()}
parse_receipt(headers) :: {:ok, map()} | {:error, term()}
amount(challenge) :: Decimal.t()
name() :: String.t()
```

| Protocol   | Module                              | Use for                                   |
| ---------- | ----------------------------------- | ----------------------------------------- |
| Xochi      | `Raxol.Payments.Protocols.Xochi`    | intent-based cross-chain (default)        |
| MPP        | `Raxol.Payments.Protocols.MPP`      | 402 micropayments                         |
| x402       | `Raxol.Payments.Protocols.X402`     | ERC-3009 TransferWithAuthorization        |
| Permit2    | `Raxol.Payments.Protocols.Permit2`  | Permit2 witness signing for solver pulls  |
| Riddler    | `Raxol.Payments.Protocols.Riddler`  | legacy B2B; delegates to Xochi            |

## Xochi cross-chain transfer

The high-level path is `transfer/4` (quote -> sign -> execute -> poll to terminal):

```elixir
alias Raxol.Payments.Protocols.Xochi
alias Raxol.Payments.Xochi.Schemas.QuoteRequest

config = %{base_url: "https://api.xochi.fi", auth: {:mandate, "0xAgent..."}}

req = %{
  wallet: MyWallet.address(),
  from_chain_id: 8453,          # Base
  to_chain_id: 1,               # Ethereum
  from_token: "0xUSDC_base",
  to_token: "0xUSDC_eth",
  from_amount: "1000000",       # 1 USDC, atomic units
  settlement_preference: "public",
  slippage_bps: 50
}

{:ok, status} = Xochi.transfer(config, req, MyWallet, [])
# status.status ∈ :completed | :failed | :refunded (terminal?)
```

Lower-level steps when you need control:

```elixir
{:ok, quote}  = Xochi.get_quote(config, req)
{:ok, signed} = Xochi.sign_intent(quote, MyWallet, req)
{:ok, exec}   = Xochi.execute_signed(config, signed)
{:ok, status} = Xochi.poll_status(config, exec.intent_id, [])
```

Cross-VM (e.g. Tron origin) uses `deposit_route_quote/3` with a `DepositRouteRequest`
(`recipient_address` required for cross-VM).

## Client auth

`Raxol.Payments.Xochi.Client` config `:auth` is one of:
`{:member, token}`, `{:mandate, agent_addr}`, `{:mandate, addr, opts}`,
`{:x402, opts}`, or `:none`. Mandate auth attaches the `X-Xochi-Delegation` header
(see `Req.Mandate` in `payments/wallets-ledger.md`).

## x402 auto-pay (HTTP 402)

On a `402`, `detect?/2` -> `parse_challenge/1` -> `build_payment/2` (signs an ERC-3009
authorization with the agent wallet) -> retry with payment headers -> `parse_receipt/1`.
Wire it into `Req` via `Raxol.Payments.Req.AutoPay` so any `Req` call transparently pays.

## Pitfalls

1. **Not polling to terminal** -- `execute` returns before settlement; poll
   `IntentStatus` until `terminal?/1`, and handle `:refunded` (check `refund_reason`).
2. **Wrong `recipient_address`** -- required for cross-VM / deposit routes; omitting it
   fails validation.
3. **Assuming Riddler is separate** -- `Protocols.Riddler` now delegates to Xochi; new
   integrations should target Xochi directly.
