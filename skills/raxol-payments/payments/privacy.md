---
title: Stealth, Privacy Tiers + ZKSAR
impact: MEDIUM
impactDescription: Requesting a privacy tier without its required attestations silently downgrades settlement to public.
tags: raxol, payments, stealth, privacy, zksar, aztec
---

# Stealth, Privacy Tiers + ZKSAR

Privacy in `raxol_payments` is trust-scored: ZK attestations produce a 0-100 trust
score, which maps to a "Glass Cube" privacy tier, which selects the settlement mode.

## Privacy tiers (`Raxol.Payments.PrivacyTier`)

```elixir
tier = Raxol.Payments.PrivacyTier.from_trust_score(score, attestations: proofs)
# tier: %{tier:, fee_bps:, settlement:, data_retention:}
```

| Tier        | Trust | Fee    | Settlement | Data retention |
| ----------- | ----- | ------ | ---------- | -------------- |
| `:standard` | 0-24  | 30 bps | public     | full           |
| `:stealth`  | 25-49 | 25 bps | stealth    | amounts        |
| `:private`  | 50-74 | 20 bps | shielded   | ranges         |
| `:sovereign`| 75+   | 15 bps | shielded   | nothing        |

`from_trust_score/2` opts: `:tier_override`, `:attestations`.
`attestation_requirements/1` lists what a tier needs; unmet requirements downgrade.
`shielded?/1` tells you when to route through the PXE bridge.

## ZKSAR attestations + trust score

```elixir
alias Raxol.Payments.Zksar
alias Raxol.Payments.Zksar.TrustScore

{:ok, verified} = Zksar.verify(proof, allowed_issuers: issuers, verify_signature: true)
{ok_list, errs} = Zksar.verify_batch(proofs, [])

score = TrustScore.aggregate(ok_list, [])   # 0-100, diminishing returns by rank
```

Proof types: `:compliance`, `:risk_score`, `:pattern`, `:attestation`, `:membership`,
`:non_membership`. Default weights favor `:non_membership` (25) and `:compliance` (20);
aggregation applies `weight / ln(rank + 1)` so stacking weak proofs has diminishing value.

## Stealth addressing (ERC-5564 / ERC-6538)

`Raxol.Payments.Xochi.Stealth` does the ECDH + view-tag work: encode/decode a
meta-address, scan for incoming stealth payments, derive the stealth address. On the
Xochi request, set `settlement_preference: "stealth"` and provide
`stealth_spending_pub_key` / `stealth_viewing_pub_key`. Claim funds via
`Xochi.Client.claim/2` with the stealth address, recipient, ephemeral pubkey, signature,
and view tag.

## Shielded settlement via Aztec PXE

For `:private`/`:sovereign` (shielded), settlement targets the Aztec Private eXecution
Environment through `Raxol.Payments.Pxe.Client`. Shielded intents carry a
`note_commitment` in their status instead of a public `tx_hash`.

## Pitfalls

1. **Tier without attestations** -- requesting `:private` without the required proofs
   downgrades to a lower tier; check `attestation_requirements/1` first.
2. **Stacking identical proofs** -- aggregation has diminishing returns; distinct proof
   *types* raise the score, duplicates barely move it.
3. **Expecting a tx_hash for shielded** -- shielded settlements expose a
   `note_commitment`; branch on `PrivacyTier.shielded?/1` / `IntentStatus.shielded?/1`.
