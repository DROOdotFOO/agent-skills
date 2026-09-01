---
title: Design System Selection
impact: MEDIUM
impactDescription: Choosing the wrong foundation means hand-rolling what an official package already solved, including its accessibility work
tags: design-system, tailwind, shadcn, radix, carbon, fluent, material, govuk, uswds, tokens
---

# Design System Selection

Pick the foundation before writing components. The decision is mostly determined by the domain, not by taste. Adapted in part from `taste-skill` (MIT, see `THIRD-PARTY-NOTICES.md`).

## Reach for the Official Package When One Exists

Some domains have an official design system that carries tokens, component behavior, and accessibility work you would otherwise redo badly.

| The project is...                        | Use                                            | Why                                                |
| ---------------------------------------- | ---------------------------------------------- | -------------------------------------------------- |
| Microsoft / enterprise SaaS              | `@fluentui/react-components`                    | Official Fluent tokens, a11y handled                |
| Google-flavored product UI               | `@material/web` + Material 3 tokens             | Official, theme-able via Material Theming           |
| IBM-style B2B analytics                  | `@carbon/react` + `@carbon/styles`              | Mature data-density patterns                        |
| Shopify app surface                      | Polaris                                         | Required for Shopify admin UI                       |
| Atlassian / Jira-style product           | `@atlaskit/*` + `@atlaskit/tokens`              | Official Atlassian DS                               |
| GitHub-style devtool or community page   | `@primer/css`, or `@primer/react-brand` for marketing | Official Primer                               |
| UK public-sector service                 | `govuk-frontend`                                | Regulatorily expected                               |
| US public-sector / trust-first           | `uswds`                                         | Same                                                |
| Accessible React foundation, no house style | `@radix-ui/themes`                           | Primitives plus a polished theme                    |
| Modern SaaS where you own the components | shadcn/ui                                       | You own the code; never ship it in default state    |
| Fast local-business or agency MVP        | Bootstrap 5.3                                   | Boring, fast, works                                 |
| Everything else                          | Tailwind utilities + project tokens             | Default for small-team builds                       |

Install commands:

```bash
npm install @material/web                              # Material Web (Material 3)
npm install @fluentui/react-components                 # Fluent UI React v9
npm install @fluentui/web-components @fluentui/tokens  # Fluent, framework-free
npm install @carbon/react @carbon/styles               # IBM Carbon
npm install @radix-ui/themes                           # Radix Themes
npm install --save @primer/css                         # Primer CSS (product UI)
npm install @primer/react-brand                        # Primer Brand (marketing UI)
npm install govuk-frontend                             # GOV.UK Frontend
npm install uswds                                      # US Web Design System
npm install bootstrap                                  # Bootstrap 5.3

npx shadcn@latest init                                 # shadcn/ui
npx shadcn@latest add button card badge separator input

yarn add @atlaskit/css-reset @atlaskit/tokens @atlaskit/button @atlaskit/badge
```

Verify the package is actually in `package.json` before importing from it. Never assume a library is present because it is popular.

## The Honesty Rule

Do not hand-recreate a design system's CSS, and do not import its tokens and then override most of them. Both produce something that looks like the system, drifts from it on every upgrade, and inherits none of its accessibility guarantees.

INCORRECT:

```css
/* Hand-rolled "Carbon-like" tokens -- drifts from the real system immediately */
:root {
  --cds-blue-60: #0f62fe;
  --cds-spacing-05: 1rem;
  --cds-body-short-01: 0.875rem;
}

.my-button {
  background: var(--cds-blue-60);
  padding: var(--cds-spacing-05);
  font-size: var(--cds-body-short-01);
}
```

CORRECT:

```tsx
// Use the real package; theme it through its documented surface
import { Button } from "@carbon/react";
import "@carbon/styles/css/styles.css";

export function Submit() {
  return <Button kind="primary">Submit</Button>;
}
```

If the brief does not match any official system, build on project tokens (see `shared/design-tokens.md`) and say plainly in a comment that the look is inspired by X rather than implying it is X.

## One System Per Project

Do not mix Fluent React with Carbon in the same tree, or drop shadcn/ui components into a Material 3 app. Two systems means two token scales, two focus-ring conventions, and two sets of upgrade breakage.

Adopting shadcn/ui specifically means you own the generated component source, so customizing radii, colors, shadows, and typography to the project is expected. Shipping it in its default state is the tell that no design decision was made.

## When the Brief Is an Aesthetic, Not a System

These have no official package. Build them with project tokens and be accurate about what they are.

| Aesthetic               | Honest implementation                                                              |
| ----------------------- | ---------------------------------------------------------------------------------- |
| Glassmorphism           | `backdrop-filter`, layered borders, highlight overlays; solid fallback under `prefers-reduced-transparency` |
| Bento tile grids        | CSS Grid with mixed cell sizes; no library owns this                                |
| Brutalism               | Native CSS, monospace, raw borders                                                  |
| Editorial / magazine    | Asymmetric grid, generous whitespace, deliberate type pairing                        |
| Dark tech / terminal    | Monospace plus one accent; see `terminal/terminal-aesthetic.md`                      |
| Mesh / aurora gradients | SVG or layered radial gradients                                                     |
| Kinetic typography      | CSS animation or scroll-driven animation; see `web/motion.md`                        |

**Apple Liquid Glass is documented for Apple platforms only.** There is no official `liquid-glass.css` for the web. Web versions are approximations built from `backdrop-filter`, layered borders, and highlights. Label them as approximations rather than implying an Apple-supported web API exists.

## Canonical Sources

Read the system's own documentation before reinventing a component. Training data lags releases, and every one of these systems has changed its token API within the last two major versions.

| System        | Documentation                                     |
| ------------- | -------------------------------------------------- |
| Material Web  | `m3.material.io`, `github.com/material-components/material-web` |
| Fluent UI     | `react.fluentui.dev`, `fluent2.microsoft.design`   |
| Carbon        | `carbondesignsystem.com`                            |
| Polaris       | `shopify.dev/docs/api/app-home/using-polaris-components` |
| Atlassian     | `atlassian.design`                                  |
| Primer        | `primer.style`                                      |
| GOV.UK        | `design-system.service.gov.uk`                      |
| USWDS         | `designsystem.digital.gov`                          |
| Tailwind      | `tailwindcss.com/docs`                              |
| Radix         | `radix-ui.com/themes/docs`                          |
| shadcn/ui     | `ui.shadcn.com`                                     |
