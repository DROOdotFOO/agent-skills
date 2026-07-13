---
title: LiveView Surface
impact: MEDIUM
impactDescription: Rendering a buffer without the a11y map or theme produces inaccessible, unstyled terminal HTML.
tags: raxol, liveview, phoenix, surface, accessibility
---

# LiveView Surface (`Raxol.LiveView`)

`raxol_liveview` (v2.6) renders the same TEA model in a Phoenix LiveView: the terminal
buffer becomes HTML (RLE spans, style-to-CSS, diff highlighting) with ARIA roles and
screen-reader announcements. Package: `packages/raxol_liveview`.

## Mount a TEA app in a LiveView

`Raxol.LiveView.TEALive` starts a `Raxol.Core.Runtime.Lifecycle` process, binds to
PubSub, routes `keydown` events into `update/2`, and re-renders on change.

```elixir
defmodule MyAppWeb.TerminalLive do
  use MyAppWeb, :live_view
  use Raxol.LiveView.TEALive, app_module: MyApp   # :app_module required
end
```

Accessibility announcements flow through the `:announcement` assign.

## Render a buffer as a component

```heex
<.live_component
  module={Raxol.LiveView.TerminalComponent}
  id="my-terminal"
  buffer={@buffer}
  theme={:synthwave84}
/>
```

Component assigns: `:buffer` (required), `:theme` (`:default`), `:width` (80),
`:height` (24), `:show_cursor` (true), `:cursor_x`/`:cursor_y` (0).

## Low-level bridge

```elixir
Raxol.LiveView.TerminalBridge.buffer_to_html(buffer,
  theme: :tokyo_night,        # nord, dracula, solarized_*, monokai, synthwave84,
                              # gruvbox_dark, one_dark, tokyo_night, catppuccin, default
  aria_mode: :log,            # :log (role=log, aria-live=polite) | :application
  a11y_map: a11y_map,
  show_cursor: true,
  cursor_position: {x, y})
```

## Pitfalls

1. **Missing `:app_module`** -- `TEALive` needs it to start the Lifecycle process.
2. **No `aria_mode` / `a11y_map`** -- output is styled but unreadable to screen
   readers; pass `:log` for streaming output, `:application` for interactive widgets.
3. **Rebuilding the whole buffer each render** -- let the bridge diff; feed it the
   updated buffer, not a fresh full-screen string, to keep RLE/diff highlighting.
