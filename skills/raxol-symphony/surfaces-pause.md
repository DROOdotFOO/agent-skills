---
title: Surfaces + Pause/Resume + Sandboxes
impact: MEDIUM
impactDescription: Without a Resumer wired to the right telemetry event, paused runs never continue.
tags: raxol, symphony, surfaces, pause, resume, sandbox
---

# Surfaces + Pause/Resume + Sandboxes

## Six surfaces

One orchestrator snapshot renders across six surfaces:

| Surface     | Module                                        | Notes                                    |
| ----------- | --------------------------------------------- | ---------------------------------------- |
| Terminal    | `Raxol.Symphony.Surfaces.Terminal`            | TEA app: active/paused/pending tables    |
| MCP         | `Raxol.Symphony.Surfaces.MCP`                 | 7 tools + `symphony://runs` resource     |
| Telegram    | `Raxol.Symphony.Surfaces.Telegram.Notifier`   | per-run HTML messages                    |
| Watch       | `Raxol.Symphony.Surfaces.Watch.Notifier`      | APNS/FCM push, high-priority bypass      |
| Web API     | `Raxol.Symphony.Web.API`                      | `GET /api/v1/state`, `/runs/:id`, ...    |
| Dashboard   | `Raxol.Symphony.Web.DashboardLive`            | Phoenix LiveView, 1s refresh             |

Register the MCP surface:

```elixir
:ok = Raxol.Symphony.Surfaces.MCP.register(orchestrator: Raxol.Symphony.Orchestrator)
# tools: symphony_list_runs / get_run / list_paused / resume_run / refresh / stop_run / get_evidence
```

## Paused-run substrate

A runner pauses by returning `{:pause, reason, token}`. `Raxol.Symphony.PauseReason`
canonicalizes reasons (the `:awaiting_*` convention):

```elixir
Raxol.Symphony.PauseReason.canonical()
# [:awaiting_request_response, :awaiting_buyer_payment, :awaiting_delivery,
#  :awaiting_evaluator_approval, :awaiting_approval, :awaiting_review]
Raxol.Symphony.PauseReason.awaiting?(:awaiting_review)   # true
```

## Resume on telemetry (ACP handoff)

The token can declare a `resume_on` spec that matches a telemetry event -- this is how a
Symphony run parks while an ACP job progresses and auto-resumes on the transition
(cross-package contract with `raxol-payments`).

```elixir
# runner pauses waiting for an ACP job to fund
Raxol.Symphony.ResumeOn.acp_pause("job-1", waiting_for: :funded, reason: :awaiting_buyer_payment)
# => {:pause, :awaiting_buyer_payment,
#     %{resume_on: %{telemetry: [:raxol, :acp, :job_session, :transition],
#                    match: %{job_id: "job-1", to: :funded}}}}

# a Resumer watches that event and resumes the matching run
{:ok, _} = Raxol.Symphony.Resumer.start_link(
  orchestrator: Raxol.Symphony.Orchestrator,
  telemetry_event: [:raxol, :acp, :job_session, :transition])
```

## Sandboxes (per-turn guardrails)

Attach to the RaxolAgent runner via `runner.agent.sandboxes`; each denies a turn that
would breach its bound:

- `Sandboxes.BudgetCap` -- caps cumulative token/cost spend per issue (`settle/3`)
- `Sandboxes.TurnRateLimit` -- max turns per sliding window per issue
- `Sandboxes.TimeOfDayWindow` -- only run within `start_hour..end_hour` (`allows?/2`)

## Pitfalls

1. **Pause with no resumer** -- a `{:pause, ...}` waiting on telemetry needs a `Resumer`
   subscribed to that exact event, or it waits forever.
2. **Mismatched `resume_on.match`** -- the event metadata must match every key; a wrong
   `job_id`/`to` silently never resumes.
3. **Watch spam** -- normal-priority pushes are debounced; only high-priority bypasses,
   so don't rely on every tick reaching the watch.
