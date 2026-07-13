---
name: raxol-payments
description: >
  Agentic commerce for Raxol agents in Elixir: the raxol_payments + raxol_acp packages
  (Xochi/Riddler/MPP/Permit2/x402 protocols, agent wallets, spend limits, stealth + privacy
  tiers, ZKSAR trust scores, and the ACP job lifecycle).
  TRIGGER when: mix.exs lists :raxol_payments or :raxol_acp; code imports Raxol.Payments.*
  or Raxol.ACP.*; user asks about agent wallets, HTTP 402 auto-pay, Xochi/Riddler cross-chain
  transfers, stealth addresses / privacy tiers, ZKSAR attestations, spend gating, or the
  ACP (Agent Commerce Protocol) job state machine / offerings.
  DO NOT TRIGGER when: writing or auditing Solidity contracts (use solidity-auditor skill);
  general Ethereum tooling / RPC / explorer questions (use ethskills skill); ZK circuit
  design in Noir (use noir skill); the core Raxol agent/TUI framework (use raxol skill);
  the Symphony orchestrator (use raxol-symphony skill).
metadata:
  author: droo
  version: "0.2.0"
  tags: elixir, raxol, payments, acp, web3, x402, xochi, stealth, wallets
---

# Raxol Payments + ACP Skill

Agentic commerce layer for Raxol agents. `raxol_payments` (v0.2) gives an agent a
wallet, a ledger with spend limits, HTTP 402 auto-pay, and the cross-chain settlement
protocols (Xochi/Riddler/MPP/Permit2/x402) plus stealth/privacy. `raxol_acp` (v0.2)
implements the Agent Commerce Protocol: a per-job state machine, service offerings, and
on-chain writes via ERC-4337 smart accounts or EOAs.

This is the Elixir *client* layer. It signs and calls; the contracts themselves are out
of scope (see `solidity-auditor`). Riddler is the payments protocol/module here
(`Raxol.Payments.Protocols.Riddler`), now delegating to Xochi.

## What You Get

- Protocol map: Xochi (default cross-chain), MPP, Permit2, x402, Riddler
- Agent wallets (env key, 1Password, ERC-4337 SCA, EOA nonce server)
- Ledger spend limits, SpendGate authorization, mandates, checkpoint idempotency
- Privacy: stealth (ERC-5564/6538), Glass Cube tiers, ZKSAR trust scores, PXE bridge
- ACP job lifecycle state machine, Offering DSL, HookClient + provider adapters
- Test patterns with the Mock provider adapter (no real chain calls)

## Two package split

| Concern                                  | Package         | Entry modules                              |
| ---------------------------------------- | --------------- | ------------------------------------------ |
| Pay for a resource / cross-chain move    | `raxol_payments`| `Protocols.Xochi`, `Ledger`, `SpendGate`   |
| Sell/deliver a job on-chain (ACP)        | `raxol_acp`     | `JobSession`, `Offering`, `HookClient`     |

## See also

- `raxol` -- core agent/TUI framework (agents, directives, MCP, workflow)
- `raxol-symphony` -- coding-agent orchestrator (uses ACP for paused-run resume)
- `solidity-auditor` -- the on-chain contracts these clients call
- `ethskills` -- Ethereum tooling, RPC, standards (ERC-4337, ERC-5564, ERC-3009)
- `noir` -- ZK circuits behind ZKSAR / shielded settlement

## Reading Guide

| Task                                    | File                          |
| --------------------------------------- | ----------------------------- |
| Move funds / pay a 402 (protocols)      | `payments/protocols.md`       |
| Stealth, privacy tiers, ZKSAR trust     | `payments/privacy.md`         |
| Wallets, ledger, spend gate, checkpoints| `payments/wallets-ledger.md`  |
| Sell a service via ACP (job lifecycle)  | `acp/job-lifecycle.md`        |
| Test without real chain calls           | `testing.md`                  |

## Key Conventions

- Amounts are atomic units as strings (`"1000000"` = 1 USDC), aggregated as `Decimal`
  in the ledger. Never pass floats.
- Every spend goes through `SpendGate.authorize/3` -> reserve -> sign -> `release`/
  `release_by_intent`. Reservations expire (TTL) and are swept.
- Wallets implement `Raxol.Payments.Wallet` (`address/0`, `sign_message/1`,
  `sign_typed_data/3`, `sign_hash/1`). Pick env/op/SCA/EOA per deployment.
- Idempotency: derive a `Checkpoint` key from canonical intent fields and check it
  before re-submitting an in-flight intent.

## Common Pitfalls

1. **Floats for money** -- use atomic-unit strings + `Decimal`; floats lose precision.
2. **Signing before gating** -- authorize/reserve budget first, or a failed send leaks
   the reservation. Always pair `authorize` with `release`/`release_by_intent`.
3. **Re-submitting on retry** -- without a `Checkpoint`, a retry double-spends; derive
   the key from intent fields and short-circuit on a hit.
4. **Real RPC in tests** -- use `Raxol.ACP.ProviderAdapter.Mock`; never a live bundler.
