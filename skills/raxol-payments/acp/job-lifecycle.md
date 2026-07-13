---
title: ACP Job Lifecycle + Offerings
impact: HIGH
impactDescription: Calling a job transition out of order (or with the wrong role) is rejected by the state machine and can strand funds.
tags: raxol, acp, job-session, offering, erc4337
---

# ACP Job Lifecycle + Offerings

`raxol_acp` implements the Agent Commerce Protocol: a per-job state machine, seller
offerings, and on-chain writes via a smart account or EOA.

## Job state machine (`Raxol.ACP.JobSession`)

One GenServer per job. States (`JobSession.Status`):

```
open -> budget_set -> funded -> submitted -> completed
                                    \-> rejected
(any) ------------------------------------> expired
```

`terminal?/1` is true for `:completed | :rejected | :expired`. `validate/2` enforces
legal transitions; `JobSession.Tools.allowed?/3` enforces which role may drive each one.

```elixir
{:ok, s} = Raxol.ACP.JobSession.start_link(
  chain_id: 8453, job_id: "job-42", role: :provider)
:ok = Raxol.ACP.JobSession.subscribe(s)

{:ok, :budget_set} = Raxol.ACP.JobSession.set_budget(s, asset_token)
{:ok, :submitted}  = Raxol.ACP.JobSession.submit(s, %{deliverable: "..."})
{:ok, :completed}  = Raxol.ACP.JobSession.complete(s, "approval msg")
status = Raxol.ACP.JobSession.get_status(s)
```

Roles are `:client`, `:provider`, `:evaluator`. `set_budget`/`fund` are client-side;
`submit` is provider-side; `complete`/`reject` are evaluator/client-side.

## Offerings (seller DSL)

`Raxol.ACP.Offering` declares a service; `handle_request/2` accepts/rejects work and
`handle_deliver/2` produces the deliverable.

```elixir
defmodule MyOffering do
  use Raxol.ACP.Offering,
    name: "my.offering", price_usdc: "0.50", sla_minutes: 5, cluster: "on_chain"

  @impl true
  def requirements_schema, do: %{type: "object", required: ["url"], properties: %{...}}
  @impl true
  def deliverables_schema, do: %{type: "object", required: ["result"], properties: %{...}}

  @impl true
  def handle_request(req, _ctx), do: {:accept, req}          # or {:reject, reason}
  @impl true
  def handle_deliver(req, _ctx), do: {:deliver, %{result: run(req)}}
end

MyOffering.register()
```

`Offering.Handler` also supports `handle_evaluate/2` for the evaluator side.

## On-chain writes (`HookClient` + provider adapters)

`Raxol.ACP.HookClient` wraps the ACP Core contract calls (`set_budget/6`, `fund/6`,
`submit/6`, `complete/6`, `reject/6`), each returning `{:ok, tx_hash}`. It writes through
a `Raxol.ACP.ProviderAdapter`:

| Adapter                          | Backend                                  |
| -------------------------------- | ---------------------------------------- |
| `ProviderAdapter.Mock`           | in-process, records calls (tests)        |
| `ProviderAdapter.JSONRPC`        | plain EOA via JSON-RPC                    |
| `ProviderAdapter.SCA`            | ERC-4337 smart account (UserOps)         |

```elixir
adapter = Raxol.ACP.ProviderAdapter.SCA.new(...)
{:ok, tx} = Raxol.ACP.HookClient.set_budget(adapter, 8453, acp_core_addr, 42, 1_000_000, <<0>>)
```

## Wallets: SCA vs EOA

- **Smart account** (`Raxol.ACP.Wallet.SCA`, ERC-4337 v0.7, Alchemy Modular Account v2):
  a session key signs UserOps, optionally sponsored by a paymaster.

  ```elixir
  defmodule MyAgent.SCA do
    use Raxol.ACP.Wallet.SCA,
      account_address: "0x..", chain_id: 8453,
      signer: MyAgent.SessionKey, signer_entity_id: 1,
      bundler_url: {:system, "ALCHEMY_BUNDLER_URL"},
      entry_point: "0x0000000071727De22E5E9d8BAf0edAc6f37da032",
      paymaster_policy_id: "my-policy"
  end
  ```

- **EOA** (`Raxol.ACP.Wallet.NonceServer`): serializes nonce assignment so concurrent
  sends never collide. `get_next/1` hands out monotonically increasing nonces.

## Pitfalls

1. **Out-of-order transitions** -- e.g. `complete` before `submit` fails `validate/2`.
2. **Wrong role** -- a `:client` cannot `complete`; check `Tools.allowed?/3`.
3. **EOA nonce race** -- multiple in-flight sends on one EOA must draw from a single
   `NonceServer` (the v2.6 fix for a fund-losing retry race), not the raw RPC nonce.
