---
title: Layout Hard Rules
impact: HIGH
impactDescription: These are mechanically checkable defects, not preferences -- each one ships a visibly broken page
tags: layout, hero, navigation, bento, grid, cta, contrast, content-density, audit
---

# Layout Hard Rules

Everything here is countable or measurable. Unlike aesthetic judgment, these can be verified by reading the markup, which is what makes them useful as an audit pass. Adapted from `taste-skill` (MIT, see `THIRD-PARTY-NOTICES.md`).

Failing any of these means shipping broken work, not merely unfashionable work.

## The Hero Fits the Viewport

The primary action must be visible without scrolling.

INCORRECT:

```tsx
<section className="pt-48">
  <p className="text-[11px] uppercase tracking-[0.2em]">EARLY ACCESS</p>
  <h1 className="text-7xl md:text-8xl leading-none">
    The operating system for modern engineering teams who ship continuously
  </h1>
  <p className="mt-6 max-w-2xl text-lg">
    We built this because every other tool assumed your team works the way the
    tool wants to work, and we think that is backwards, so we started over with
    a model that adapts to how you already operate.
  </p>
  <div className="mt-8 flex gap-3">
    <button>Get started</button>
    <button>Let's talk</button>
  </div>
  <p className="mt-4 text-xs">Works with GitHub, GitLab, and self-hosted Git</p>
  <div className="mt-6 flex gap-8">{/* trust logos */}</div>
</section>
```

CORRECT:

```tsx
<section className="pt-24">
  <h1 className="text-4xl md:text-5xl lg:text-6xl tracking-tight">
    Ship continuously, without the ceremony
  </h1>
  <p className="mt-6 max-w-[55ch] text-lg">
    Plan, review, and release from one place. Works with the Git host you
    already use.
  </p>
  <div className="mt-8 flex gap-3">
    <button>Get started</button>
    <button>See how it works</button>
  </div>
</section>
```

The checkable constraints:

| Constraint            | Limit                                                       |
| --------------------- | ----------------------------------------------------------- |
| Headline              | Max 2 lines at desktop                                       |
| Subtext               | Max 20 words AND max 4 lines                                 |
| Top padding           | Max `pt-24` (~6rem) at desktop                               |
| Text elements         | Max 4 total                                                  |
| Primary CTA           | Exactly 1, plus at most 1 secondary                          |
| Font scale            | `text-4xl md:text-5xl lg:text-6xl` typical; `text-6xl md:text-7xl` only for 3-5 word headlines |

A four-line hero headline is a font-size error, not a copy-length error. Plan the headline scale and the hero asset size together.

Banned inside the hero, all of which belong in sections below it: a tagline under the CTAs, a trust micro-strip, a pricing teaser, a feature bullet list, a social-proof avatar row, and the "Used by / Trusted by" logo wall.

If more breathing room is wanted, increase the font or asset scale. Increasing top padding past `pt-24` makes the content float halfway down the viewport and reads as a layout bug.

## Navigation Renders on One Line

At `lg` (1024px) the nav fits on a single line, and its height is at most 80px (64-72px typical). If items do not fit, shorten labels, drop secondary items, or collapse to a menu. A two-line desktop nav is broken; a nav bar eating 15% of the viewport is broken.

## Eyebrow Ratio

Count the small uppercase tracked labels sitting above section headings across all components. The hero counts as one.

```
eyebrowCount <= ceil(sectionCount / 3)
```

A nine-section page gets at most three. If section A has an eyebrow, the next two do not. The alternative to an eyebrow is no eyebrow -- a section's position on the page already categorizes it.

## Layout Family Variety

Two countable rules:

- **Repetition ban.** Once a layout family is used (three-column cards, full-width quote, split text/image), it appears at most once more. An eight-section page uses at least four distinct families.
- **Zigzag cap.** Alternating left-image/right-text and its mirror is fine twice. The third consecutive image-and-text split fails. Break it with a full-width section, a vertical stack, a grid, or a different family entirely.

Related: the three-equal-feature-cards row is the default reach for any "features" section. Prefer an asymmetric grid, a two-column zigzag, or a horizontal-scroll treatment.

## Bento Cell Count Matches Content

A grid has exactly as many cells as there is content for. Three items produce three cells; five items produce five. An empty cell in the middle or trailing at the end means the grid shape was chosen before the content was counted -- reshape the grid rather than pasting a blank tile.

Multi-cell grids also need visual variation. Six white cards containing only text reads as a default even when the rest of the page is strong; at least two or three cells should carry a real image, a pattern, or a tinted background.

## Split Headers

The pattern of a large left headline with a small explainer paragraph floating in the right column is a default reach. A section should carry one focused message. If both a headline and an explainer are genuinely needed, stack them vertically at `max-w-[65ch]`.

The degenerate version -- a tiny paragraph floating in the top-right corner of a section header, aligned to nothing -- is always wrong.

## CTA Discipline

INCORRECT:

```tsx
<nav><button>Get in touch</button></nav>
<section><button className="max-w-[7rem]">VIEW SELECTED WORK</button></section>
<footer><button>Let's talk</button></footer>
```

CORRECT:

```tsx
<nav><button>Contact</button></nav>
<section><button>View work</button></section>
<footer><button>Contact</button></footer>
```

- **No wrapping.** A CTA label fits on one line at desktop. Fix by shortening the label (three words max, ideally one or two) or by removing the width constraint. Never by shrinking the text.
- **One label per intent.** "Get in touch", "Contact us", "Let's talk", "Start a project", and "Reach out" are one intent. Pick one label and use it in the nav, the body, and the footer. Same for signup intent and portfolio intent.

## Contrast Is Checked, Not Assumed

Every interactive element is verified against its actual background before shipping. WCAG AA: 4.5:1 for body text, 3:1 for large text (18px+).

INCORRECT:

```tsx
// White label on a white surface; ghost button invisible over the photo
<button className="bg-white text-white">Get started</button>
<button className="bg-transparent text-white">Learn more</button>
```

CORRECT:

```tsx
<button className="bg-zinc-900 text-zinc-50">Get started</button>
<button className="border border-white/60 bg-black/30 text-white backdrop-blur-sm">
  Learn more
</button>
```

The same check applies to form inputs, placeholder text, helper text, error text, and focus rings against their section background. Light placeholders on a near-white form is the most common form failure.

Ghost buttons over photography need a scrim, a backdrop, or a stroke -- the photo's brightness is not under your control.

## Consistency Locks

Three properties are chosen once and hold for the whole page. Each is verified by scanning every component.

| Lock          | Rule                                                                         |
| ------------- | ---------------------------------------------------------------------------- |
| Theme         | One theme for the page. No light section between dark sections. A deliberate one-time theme switch is allowed if the brief calls for it. |
| Accent color  | One accent everywhere. A warm-grey page does not grow a blue CTA in section 7, and a rose page does not grow a teal badge in the footer. |
| Corner radius | One radius scale. Mixed systems only with a documented rule ("pills for buttons, 16px for cards, 8px for inputs") followed everywhere. |

Section-level background tints within one theme family are fine (`bg-zinc-950` beside `bg-zinc-900`). Flipping to `bg-amber-50` mid-page is not.

## Content Density

Default shape per section: a headline of 8 words or fewer, a sub-paragraph of 25 words or fewer, and one visual or one action. More than that needs justification from the section's job.

Long lists need a different component, not a longer list. Past five items, a default `<ul>` with `divide-y` rows is the lazy choice:

- Group into two or three labeled clusters with sparse dividers
- Card grid with an image or figure per item
- Tabs or an accordion when items are categorizable
- Horizontal scroll-snap pills
- Featured-plus-rest: three or four items as display tiles, the remainder behind a disclosure

A ten-row specification table with a hairline under every row is the worst available default. Also avoid `border-t` and `border-b` on the same rows -- pick one and use it sparingly.

Twenty-row data tables, thirty-row award lists, and full pricing matrices do not belong on a marketing page. Show the top three to five and link to the rest, or accept that the data is the product and give it its own page.

## Quotes

Max three lines of quote body. A landing-page quote is a snippet; if the source is longer, cut it. Attribution carries name plus role, optionally company -- never a bare first name. Use real typographic quote marks or none.

## Structural Requirements

- **Viewport stability**: `min-h-[100dvh]`, never `h-screen`. The iOS Safari address bar makes `vh` jump.
- **Grid over flex math**: `grid grid-cols-1 md:grid-cols-3 gap-6`, not `w-[calc(33%-1rem)]`.
- **Explicit mobile collapse**: every multi-column layout declares its sub-768px fallback in the same component. "Tailwind will handle it" is not a fallback.
- **Full state coverage**: loading (skeletons shaped like the final layout, not spinners), empty (composed, showing how to populate), and error (inline for forms, contextual for transient).
- **Labels above inputs**, helper text present in markup, error text below. Never placeholder-as-label.
