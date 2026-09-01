---
title: Pre-Flight Check
impact: CRITICAL
impactDescription: The audit is only real if it runs as a checklist; skipped boxes are how known defects ship
tags: checklist, pre-flight, audit, qa, ship-gate, verification
---

# Pre-Flight Check

Run before declaring a page done. Each group is ordered cheapest-check-first, so a failing page fails fast. Adapted from `taste-skill` (MIT, see `THIRD-PARTY-NOTICES.md`).

Report results as a list of failures with file and line, not as a pass/fail verdict on the whole page. A page with three failures needs three fixes, not a rewrite.

## Group 1: Mechanical Counts

These are countable by reading the markup. Do them first -- they need no judgment and catch the most common defects.

- [ ] **Zero em-dashes (`—`) and zero en-dash separators (`–`)** in any visible string: headlines, eyebrows, pills, body, quotes, attribution, captions, buttons, alt text. See `ai-tells.md`.
- [ ] **Eyebrow count** <= `ceil(sectionCount / 3)`, hero counted as one. Grep for `uppercase tracking` and similar small-caps labels above headings.
- [ ] **Layout families**: no family repeated more than twice; at least 4 distinct families across 8 sections.
- [ ] **Zigzag cap**: no 3+ consecutive sections using the image-and-text split.
- [ ] **Bento cell count** equals item count. No empty cell mid-grid or trailing.
- [ ] **Marquees**: at most one per page.
- [ ] **Duplicate CTA intent**: no two labels expressing the same intent anywhere on the page.
- [ ] **Middle dots (`·`)**: at most one per metadata line, not used as the default separator.
- [ ] **Decorative status dots**: zero, unless conveying real semantic state.

## Group 2: Hero

- [ ] Headline <= 2 lines at desktop.
- [ ] Subtext <= 20 words AND <= 4 lines.
- [ ] Primary CTA visible without scrolling.
- [ ] Top padding <= `pt-24` at desktop.
- [ ] <= 4 text elements total (eyebrow OR brand strip, headline, subtext, CTAs).
- [ ] No tagline under the CTAs, no trust micro-strip, no pricing teaser, no feature bullets, no avatar row.
- [ ] "Used by / Trusted by" logo wall sits **under** the hero, not inside it.
- [ ] No version label (`V0.6`, `BETA`, `INVITE-ONLY`) unless the brief is a launch.
- [ ] Hero carries a real visual. Text plus a gradient blob is a placeholder, not a hero.
- [ ] Font scale planned against asset size -- a 4-line headline is a font-size error.

## Group 3: Consistency Locks

- [ ] **Theme lock**: one theme across the page; no section inverts mid-scroll.
- [ ] **Accent lock**: one accent color used identically in every section.
- [ ] **Shape lock**: one corner-radius system, or a documented mixed rule followed everywhere.
- [ ] **Icon lock**: one icon family, one global stroke width, no hand-rolled SVG paths.
- [ ] **One design system**: no mixing (e.g. Material components inside a shadcn tree).

## Group 4: Accessibility and Contrast

Never assume; verify against the actual rendered background.

- [ ] Every CTA label passes WCAG AA against its own button background (4.5:1 body, 3:1 for 18px+).
- [ ] Ghost buttons over photography have a scrim, backdrop, or stroke.
- [ ] Form inputs, placeholders, helper text, error text, and focus rings all pass AA against the section background.
- [ ] No CTA label wraps to 2+ lines at desktop.
- [ ] Labels above inputs; error text below; no placeholder-as-label.
- [ ] Focus indicators present on every interactive element.
- [ ] No pure `#000000` or `#ffffff` as page background or body text.
- [ ] Color is never the only signal for state.

## Group 5: Content

- [ ] **Copy self-audit**: every visible string re-read. No grammatically broken phrases, unclear referents, or metaphors that do not track.
- [ ] No placeholder names (`John Doe`), brands (`Acme`, `Nexus`), or fake-perfect numbers (`99.99%`).
- [ ] No filler verbs (`Elevate`, `Seamless`, `Unleash`, `Next-Gen`).
- [ ] No performative-craftsman labels (`From the field`, `On our desks`, `Quietly in use at`).
- [ ] Invented spec numbers are either sourced, marked as sample, or removed.
- [ ] Quotes <= 3 lines; attribution has name plus role, not a bare first name.
- [ ] Sub-paragraphs <= 25 words by default.
- [ ] Lists over 5 items use a real component, not `divide-y` rows.
- [ ] No 20-row data tables or full pricing matrices on a marketing page.
- [ ] Logo wall shows logos only -- no category labels underneath.

## Group 6: Visual Assets

- [ ] Real images used. No `<div>`-based fake screenshots, fake terminals, or fake dashboards.
- [ ] No hand-rolled decorative SVG illustrations as filler.
- [ ] No pills, tags, or labels overlaid on photographs.
- [ ] No photo-credit captions unless crediting a real photographer.
- [ ] Missing assets are labeled TODO slots and reported, not papered over.
- [ ] Multi-cell grids have at least 2-3 cells with real visual variation.

## Group 7: Motion

Skip this group entirely if the page is deliberately static. A static page is a valid outcome; half-built motion is not.

- [ ] Every animation justifiable in one sentence (hierarchy, storytelling, feedback, state transition).
- [ ] No `window.addEventListener("scroll")`, no `window.scrollY` in React state, no `rAF` loop touching state.
- [ ] No `useState` driving continuous pointer or scroll values.
- [ ] Only `transform` and `opacity` animated.
- [ ] Pinned sections use `start: "top top"` with `pin: true`.
- [ ] Scroll effects have cleanup (`ctx.revert()` or equivalent) and are isolated in client leaf components.
- [ ] `prefers-reduced-motion` honored; loops, parallax, and hijacks collapse to static.
- [ ] Grain and noise overlays only on fixed `pointer-events-none` elements.
- [ ] If the page claims motion, it actually moves.

See `design-ux` skill, `web/motion.md`, for the correct implementations.

## Group 8: Structural and Performance

- [ ] `min-h-[100dvh]`, never `h-screen`.
- [ ] Grid used instead of flexbox percentage math.
- [ ] Mobile collapse declared explicitly per multi-column section.
- [ ] Navigation on one line at desktop, height <= 80px.
- [ ] Loading, empty, and error states all present.
- [ ] Z-index used systemically, not as scattered guesses.
- [ ] Dark mode tokens defined and visually checked in both modes.
- [ ] Core Web Vitals plausible: LCP < 2.5s, INP < 200ms, CLS < 0.1.
- [ ] Every imported package actually present in `package.json`.

## Reporting

A finding is only useful if it is actionable. For each failure report the rule, the location, and the fix:

```
layout-hard-rules / eyebrow ratio
  app/page.tsx:34,71,96,118,140  -- 5 eyebrows across 7 sections (limit: 3)
  Fix: drop the eyebrows on Capabilities, Process, and Contact.

ai-tells / em-dash
  components/Hero.tsx:12  -- "Built for teams — not for demos"
  Fix: replace with a comma.
```

Do not report a rule as violated without pointing at the specific line. Do not pad the report with rules that passed.
