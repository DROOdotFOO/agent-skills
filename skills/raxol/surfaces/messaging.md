---
title: Messaging Surfaces
impact: HIGH
impactDescription: Chat/notification surfaces are projections of a TEA app; wiring them as bespoke bots instead of adapters duplicates routing, auth, and session logic and breaks the "same model everywhere" invariant.
tags: raxol, gateway, telegram, watch, surface, chat, notifications
---

# Messaging Surfaces (Gateway / Telegram / Watch)

Chat and notification channels are rendering surfaces over the same TEA model,
exactly like the terminal, LiveView (`surfaces/liveview.md`), and MCP
(`mcp/server.md`). The TEA app does not know it is talking to Telegram, Discord,
or an Apple Watch -- an adapter translates inbound platform events into Raxol
events and projects the model's rendered frame back into a platform payload.

Three packages, one shape: **input event -> `update/2` -> rendered frame ->
outbound payload**, one supervised process per chat.

| Package          | Surface                                   | Per-chat runtime                          |
| ---------------- | ----------------------------------------- | ----------------------------------------- |
| `raxol_gateway`  | "Reach": N chat platforms, one contract   | `Gateway.Session` (handler)               |
| `raxol_telegram` | Telegram: `<pre>` + inline keyboards      | `Core.Runtime.Lifecycle` per chat         |
| `raxol_watch`    | Apple Watch (APNS) / Wear OS (FCM) push   | no per-chat process; push + tap-back      |

## Gateway: one daemon, many platforms (`raxol_gateway`)

One supervised daemon connects many chat platforms through a single adapter
contract, with process-per-chat sessions and a unified session key.

### The session key

`Raxol.Gateway.Route` is the routing tuple; `Route.key/1` is the stable identity
sessions are keyed by:

```elixir
route = Raxol.Gateway.Route.new(%{
  platform: :telegram, chat_type: :group, chat_id: -1001234567890, user_id: 42
})
Raxol.Gateway.Route.key(route)
# "agent:main:telegram:group:-1001234567890"
```

`{:platform, :chat_type, :chat_id}` are enforced keys; `:user_id` is optional.
The key is what a cross-platform `SessionRouter.handoff/3` rebinds so a
conversation log resumes on another platform.

### The adapter contract (frozen, ADR-0023)

Adding a platform is implementing `Raxol.Gateway.Adapter` -- five callbacks that
own only platform I/O and translation. Routing, sessions, auth, and history stay
in the gateway:

```elixir
@callback connect(config()) :: {:ok, conn()} | {:error, term()}
@callback disconnect(conn()) :: :ok
@callback platform() :: atom()                                    # :telegram, :discord, ...
@callback normalize_event(raw()) :: {:ok, Route.t(), event()} | :ignore
@callback send_message(conn(), Route.t(), rendered()) :: :ok | {:error, term()}
```

`Raxol.Gateway.Adapter.InMemory` is the reference adapter (use it in tests).
Shipped adapters: Telegram (`Raxol.Telegram.GatewayAdapter`), Discord
(`Adapter.Discord` REST + `Discord.GatewaySocket` v10 feed), Email
(`Adapter.Email`, outbound SMTP only). The contract is frozen: additions must be
optional callbacks.

### Per-chat handler

A `Raxol.Gateway.Session` (one process per chat, idle timeout) runs a
`Raxol.Gateway.Handler` -- `init/2` + `handle_event/2`, optional `terminate/2`
for clean stops:

```elixir
@callback init(Route.t(), keyword()) :: {:ok, state()} | {:error, term()}
@callback handle_event(event(), state()) ::
            {:reply, rendered(), state()} | {:noreply, state()}
@callback terminate(reason :: term(), state()) :: term()   # optional; clean stops only
```

Two handlers ship:
- `Handler.Agent` -- agent conversations.
- `Handler.Lifecycle` -- a **full TEA app per chat** under `environment: :gateway`.

`environment: :gateway` starts no terminal driver, no plugin manager, and
registers no process names, so one app module serves any number of chats
concurrently. `handle_event/2` translates the gateway event to a Raxol event,
casts it into the app's dispatcher, and collects the app's next rendered frame
as plain text. It requires the optional `:raxol` dep (`{:error, :raxol_not_loaded}`
without it).

```elixir
{Handler.Lifecycle, app_module: MyApp.CounterApp}   # options: :width/:height (80x24),
#   :render_timeout_ms (5000), :event_fn, :format_fn, :lifecycle_opts
```

Turn collection is deterministic: stale frames are flushed, the event is cast, a
`:sys` barrier confirms the model fold, a synchronous engine render draws it, and
the newest frame wins. Frames rendered *between* turns are discarded -- a chat
surface replies to messages; spontaneous pushes are `Gateway.Delivery`'s job.

### Supervision and outbound

```elixir
{Raxol.Gateway.Supervisor, handler: {Handler.Lifecycle, app_module: MyApp}}
```

`:rest_for_one` over `Pairing` (DM pairing codes + allowlists), a
`DynamicSupervisor` of sessions, and `SessionRouter` (keyed by `Route.key/1`;
`:max_sessions` 1000, `:idle_timeout` 10 min, `:cooldown_ms` 5s per key).

`Raxol.Gateway.Delivery.deliver/3` sends a rendered message to one of four
destinations against a `%{platform => {adapter, conn}}` map: `{:direct, route}`,
`{:home, route}` (cron/background results), `{:cross_platform, route}`, or
`{:target, "telegram:-1001234567890"}` (explicit string; platform must match a
connected adapter -- no `String.to_atom/1`).

## Telegram: `<pre>` + inline keyboards (`raxol_telegram`)

The Telegram surface renders each chat's TEA app as a monospace `<pre>` HTML
block with an inline keyboard for navigation. One `Core.Runtime.Lifecycle` per
chat (sessions auto-expire after 10 min; `SessionRouter` caps `max_sessions`,
default 1000).

```elixir
{Raxol.Telegram.Supervisor, app_module: MyApp.CounterApp}   # or max_sessions: 500
```

Wire `Raxol.Telegram.Bot.handle_update/2` into a Telegex poll loop or webhook:

```elixir
def handle_update(update), do: Raxol.Telegram.Bot.handle_update(update, allowed_chat_ids: [123])
```

The bot handles `/start` and `/stop` directly; other text and callback-query
taps are translated to Raxol events and routed to the per-chat session.
`allowed_chat_ids: [...]` restricts chats (nil = allow all); unlisted chats are
silently dropped with a `[:raxol_telegram, :bot, :denied]` telemetry event.

### Output projection

`Raxol.Telegram.OutputAdapter` turns a screen buffer into a Telegram payload:

```elixir
{html, keyboard} = Raxol.Telegram.OutputAdapter.format_message(buffer, view_tree)
# html: "<pre>...escaped monospace frame...</pre>"
# keyboard: default nav rows (arrows/Tab/Space/Enter/Quit as "key:left" callback_data)
#           plus one row per view-tree :button node ("btn:{id}" callback_data)
```

Buttons in the view tree become extra inline-keyboard buttons; a tap on
`"btn:{id}"` or `"key:left"` comes back through `Bot.handle_update/2` as a
callback query and is dispatched into `update/2`. Re-renders edit the existing
message to avoid spam. Default render size is 40x20.

### Guardian: admin-bot join-request screening

`Raxol.Telegram.Guardian` is a separate surface (ADR-0014) for the admin-bot
role -- it does **not** run a TEA app. A single `screen/1` callback decides what
happens to a `chat_join_request`:

```elixir
defmodule MyApp.SpamFilter do
  @behaviour Raxol.Telegram.Guardian

  @impl true
  def screen(applicant) do
    cond do
      blocked?(applicant.user_id) -> {:decline, "banned"}
      missing_bio?(applicant)     -> {:ask_mini_app, "https://verify.myapp.com", "Verify"}
      true                        -> {:approve, nil}
    end
  end
end
```

`Guardian.decide/2` runs the configured module (app env `:guardian`, default
`Guardian.Static` which approves everyone); `Guardian.apply_decision/3` calls the
Bot API. With a `query_id` (Bot API 10.1+) it uses `answerChatJoinRequestQuery`,
falling back to `approveChatJoinRequest`/`declineChatJoinRequest` on a
`:bot_api_error`. `:ask_mini_app` is a hand-off: it DMs the applicant a `web_app`
button; the consumer-hosted mini-app makes the final call. `Guardian.MCPTools.register/0`
exposes approve/decline/screen/list_pending over `Raxol.MCP.Registry` (opt-in;
needs `raxol_mcp`) so external agents can override decisions.

## Watch: glanceable push + tap-back (`raxol_watch`)

The watch is a push-only surface: model state and accessibility announcements
project into platform notification payloads (Apple Watch via APNS, Wear OS via
FCM), and tap actions route back into the TEA app as events. There is no per-chat
process -- the `Notifier` fans a notification out to all registered devices.

```elixir
{Raxol.Watch.Supervisor, push_backend: Raxol.Watch.Push.APNS}
# :rest_for_one over DeviceRegistry + Notifier

Raxol.Watch.DeviceRegistry.register("token_abc", :apns)
Raxol.Watch.DeviceRegistry.register("token_xyz", :fcm, high_priority_only: true)
```

### Projecting model -> notification

```elixir
# Accessibility announcement (Notifier auto-subscribes to Core.Accessibility)
Raxol.Watch.Formatter.format_announcement("Build failed", :high)

# Model-state summary (glanceable key/value rows)
Raxol.Watch.Formatter.format_model_summary("Dashboard", [{"CPU", "42%"}, {"Reqs", "847/s"}])
|> Raxol.Watch.Notifier.push_to_all()
```

`Formatter` truncates `:body` to 160 chars for the glance while preserving the
full text under `:body_long`; rich constructors add voice/image/sticker/location
attachments encoded per-platform in the backend (`mutable-content`,
`interruption-level` for APNS; `image` field + JSON-encoded data for FCM).

### Backend behaviour

```elixir
@callback push(device_token :: String.t(), notification :: map()) :: :ok | {:error, term()}
```

Implementations: `Push.APNS`, `Push.FCM`, `Push.Noop` (tests). Platform
differences live in the backend, not on consumers.

### Debounce and dead-token prune

The `Notifier` debounces normal-priority pushes (1s, coalescing) to respect
watch battery; `:high` priority bypasses debouncing and pushes immediately.
Pushes fan out via `Task.async_stream` (max_concurrency 10). On a **permanent**
backend failure (APNS `:bad_device_token`, `:unregistered`, `:expired_token`,
`:device_token_not_for_topic`; FCM `:invalid_argument`, `:sender_id_mismatch`)
the device is auto-unregistered with reason `:delivery_failed`. Transient
failures (`:too_many_requests`, server errors) leave the device registered.

### Tap-back -> event

`Raxol.Watch.ActionHandler` maps a tapped action ID to a `Raxol.Core.Events.Event`
and routes it as `{:watch_action, event}`:

```elixir
Raxol.Watch.ActionHandler.dispatch("details", to: MyApp.TEA)
# handle_action("details") => %Event{type: :key, data: %{key: :enter}}
```

Default action map includes nav (`pause`/`details`/`next`/`quit`) and chat
(`mute`/`pin`/`delete` as `:custom`; `dismiss` -> nil). Quick-reply text input
(iOS `UNTextInputNotificationAction` / Android `RemoteInput`) arrives via
`handle_reply_action/3` -> `Event.new(:reply, %{action: id, text: text})`.
Dispatcher `:to` accepts a pid, registered name, `{mod, fun}`, `{mod, fun, extra}`,
or a 1-arity fn; falls back to app env `:action_dispatcher`.

## Common Pitfalls

1. **Writing a bespoke bot instead of an adapter** -- put platform I/O in a
   `Gateway.Adapter` (5 callbacks) and let the gateway own routing/auth/sessions.
   Re-implementing per-chat routing duplicates `SessionRouter`.
2. **Expecting a per-chat TEA app on the watch** -- `raxol_watch` is push +
   tap-back, not a Lifecycle per device. Notifications fan out to all devices.
3. **Guardian is not a TEA app** -- `screen/1` is a pure decision; it screens
   join requests, it does not render a chat surface. Keep it decoupled.
4. **Spontaneous pushes from a gateway session** -- `Handler.Lifecycle` discards
   frames rendered between turns; use `Gateway.Delivery` (`:home`/`:target`) for
   unsolicited output, not the reply path.
5. **`environment: :gateway` needs `:raxol`** -- `Handler.Lifecycle.init/2`
   returns `{:error, :raxol_not_loaded}` without the optional dep.
6. **`{:target, "..."}` platform must be connected** -- delivery matches the
   string prefix against connected adapter atoms; it never `String.to_atom/1`s
   the target.

## Boundary

These packages and their adapters live in the **raxol** skill. Symphony's
tracker-driven *use* of the Telegram and Watch surfaces (routing run evidence and
paused-run prompts to chat/watch) belongs to `raxol-symphony`. Payments/ACP over
chat belong to `raxol-payments`.

## See also

- `surfaces/liveview.md` -- the browser projection of the same TEA model
- `mcp/server.md` -- the MCP-tool projection
- `agents/tea-agent.md` -- the `update/2` / model these surfaces render
