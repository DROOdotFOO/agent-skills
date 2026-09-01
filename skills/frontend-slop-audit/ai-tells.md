---
title: AI Tells
impact: HIGH
impactDescription: These patterns are the signatures that mark a page as machine-generated regardless of how well the rest is built
tags: ai-tells, anti-slop, audit, copy, decoration, em-dash, placeholder-content
---

# AI Tells

> **Observed AI defaults as of 2026-09. These are empirical, not timeless -- re-verify annually.**
>
> This catalog was mined from repeated production failures, not derived from principle. As models change, some entries will stop being defaults and new ones will appear. Treat a stale entry as noise, not as law. Adapted from `taste-skill` (MIT, see `THIRD-PARTY-NOTICES.md`).

A "tell" is a pattern that is not wrong in isolation but appears so reliably in generated output that its presence identifies the author. Each one below has a legitimate use; the failure is reaching for it by default.

## The Em-Dash

The em-dash is the single most reliable tell in generated prose. The rule is binary because graduated phrasing ("use sparingly") has consistently failed to change behavior.

INCORRECT:

```html
<h1>Built for teams — not for demos</h1>
<p>We ship weekly — sometimes daily — and every release is reversible.</p>
<figcaption>— Sarah Okonkwo, Head of Platform</figcaption>
```

CORRECT:

```html
<h1>Built for teams, not for demos</h1>
<p>We ship weekly, sometimes daily. Every release is reversible.</p>
<figcaption>Sarah Okonkwo, Head of Platform</figcaption>
```

Banned in headlines, eyebrows, labels, pills, button text, body copy, captions, quote attribution, nav items, and alt text. The en-dash (`–`) is banned as a separator too: ranges use a plain hyphen (`2018-2026`, `40-80k`). The only permitted dash characters are the hyphen and the minus sign.

This applies to visible page text. It is a page-content rule, not a source-code rule.

## Decorative Micro-Labels

The small uppercase wide-tracked label above a section heading. Typical signature: `text-[11px] uppercase tracking-[0.18em]`.

INCORRECT:

```tsx
<section>
  <p className="text-[11px] uppercase tracking-[0.22em]">002 · Capabilities</p>
  <h2>What we do</h2>
  <p className="text-sm">
    Each of these is something we ship today, not a roadmap promise. The list
    will stay short on purpose.
  </p>
</section>
```

CORRECT:

```tsx
<section>
  <h2>What we do</h2>
</section>
```

Three separate tells stack in that example:

- **Section-number eyebrows.** `00 / INDEX`, `001 · Capabilities`, `06 · how it works`, `Index of Work, 2018-2026`. If the reader can count, the number adds nothing.
- **Eyebrow saturation.** An eyebrow above every heading produces a templated rhythm. Cap at one per three sections; see `layout-hard-rules.md`.
- **Micro-meta sentences.** A small explanatory sentence under the heading commenting on the section's own restraint. Eyebrow plus headline plus body is already enough.

## Atmospheric Decoration

Text that exists to make the page feel designed rather than to inform.

| Pattern                       | Example                                              | Instead                                   |
| ----------------------------- | ---------------------------------------------------- | ----------------------------------------- |
| Locale / time / weather strip | `LIS 14:23 · 18°C`, `Lisbon, working with founders`  | Drop it. A footer address is fine.        |
| Scroll cue                    | `Scroll`, `↓ scroll to explore`, animated mouse icon | Drop it. The reader knows how to scroll.  |
| Hero decoration strip         | `BRAND. MOTION. SPATIAL.`, `DESIGN · BUILD · SHIP`   | Drop it, unless the strip carries real links |
| Version label in hero         | `V0.6`, `BETA`, `INVITE-ONLY PREVIEW`                | Only when the brief is a launch           |
| Version footer on marketing   | `v1.4.2`, `Build 0048`, `last sync 4s ago · main`    | Drop it. That is devtool fixture content. |
| Photo-credit caption          | `Field study no. 12 · Ines Caetano`, `Frame XII · 35mm` | Only credit a real photographer        |
| Live-stock counter            | `Reservation 412 of 800`                              | Only with real inventory data             |
| Rotated vertical text         | `INDEX OF WORK` turned 90 degrees                     | Only for genuinely experimental briefs    |
| Decorative crosshairs/hairlines | Grid lines drawn to look designed                   | Only when they organize real content      |

The middle dot (`·`) is rationed to one per metadata line. `foo · bar · baz · qux` as a default separator is itself a tell; prefer line breaks, hairlines, or columns.

Colored status dots before nav links, list rows, or badges are banned unless the dot conveys real semantic state (actual server status, a real availability flag), and then only sparingly.

## Fake Product Previews

Building a product screenshot out of styled `<div>` elements is the most recognizable structural tell.

INCORRECT:

```tsx
// A "dashboard" assembled from divs -- reads as fake at any size
<div className="rounded-xl border bg-white p-4 shadow-2xl">
  <div className="flex gap-1.5">
    <span className="h-3 w-3 rounded-full bg-red-400" />
    <span className="h-3 w-3 rounded-full bg-yellow-400" />
    <span className="h-3 w-3 rounded-full bg-green-400" />
  </div>
  <div className="mt-4 space-y-2">
    <div className="h-3 w-3/4 rounded bg-zinc-200" />
    <div className="h-3 w-1/2 rounded bg-zinc-200" />
  </div>
  <p className="mt-4 text-[10px] text-zinc-400">v0.6.2-rc.1 · last sync 4s ago</p>
</div>
```

CORRECT:

```tsx
// A real screenshot, or a real mini-instance of the component, or nothing
<img
  src="/product/board-view.png"
  alt="Board view showing three columns of in-progress work"
  width={1600}
  height={1000}
/>
```

If no real asset exists, leave a labeled slot (`{/* TODO: product screenshot, 1600x1000 */}`) and say so in the response. Do not fill the gap with fake UI, and do not fill it with hand-drawn decorative SVG either. Icons from a library are fine; invented illustrations as filler are not.

A pure-text page with gradient blobs is not minimalism, it is an incomplete page.

## Placeholder Content

INCORRECT:

```tsx
const testimonials = [
  { name: "John Doe", company: "Acme Corp", metric: "50%" },
  { name: "Jane Smith", company: "Nexus", metric: "99.99%" },
];
```

CORRECT:

```tsx
const testimonials = [
  { name: "Priya Raghunathan", company: "Kettleford Logistics", metric: "47.2%" },
  { name: "Tomas Bergqvist", company: "Vinter Analytics", metric: "3.1x" },
];
```

- **Names**: no `John Doe` / `Jane Smith` / `Sarah Chan`. Use realistic, locale-appropriate names.
- **Brands**: no `Acme` / `Nexus` / `SmartFlow` / `Cloudly`. Invent names that sound like real companies.
- **Numbers**: no `99.99%` / `50%` / `1234567`. Real data reads messy.
- **Avatars**: no generic user glyphs standing in for people.

Fake-precise numbers cut both ways. A spec like `5.8 mm` or `4.1x` is fine when it comes from the brief or real data, and fine when explicitly marked as sample. Inventing engineering precision the brand never claimed is not.

## Marketing Copy Tells

| Pattern                                    | Why it reads as generated                          |
| ------------------------------------------ | --------------------------------------------------- |
| "Quietly in use at", "Quietly trusted by"   | Performative understatement; use "Trusted by" or nothing |
| "From the field", "Field notes", "On our desks", "Currently on the bench" | Performative craftsman labels on ordinary sections |
| "Elevate", "Seamless", "Unleash", "Next-Gen", "Revolutionize", "Delve" | Filler verbs with no referent |
| Mock-humble industry asides                 | Cute, and transparently machine-written             |
| Poetic wordplay in UI labels                | Reads as an author trying to sound thoughtful       |

Before shipping, re-read every visible string -- headlines, subheads, button labels, body, captions, alt text, error messages -- and flag any that is grammatically broken, has an unclear referent, or contains a metaphor that does not track. Rewrite each flagged string. If you are unsure whether a phrase makes sense, replace it with a plain functional sentence. Boring and correct beats clever and wrong.

## Visual Defaults

- **No pure black (`#000000`) or pure white (`#ffffff`)** as page background or body text. Use off-black and off-white.
- **No neon or outer glows** by default. Prefer inner borders and tinted shadows.
- **No gradient text on large headings.**
- **No custom mouse cursors.** Accessibility-hostile and performance-hostile.
- **No pure-black drop shadows on light backgrounds.** Tint the shadow toward the background hue.
- **No hand-rolled SVG icon paths.** Use an icon library, one family per project, with a single global stroke width.
- **No pills or tags overlaid on photographs.** Caption below the image instead.

### Typography defaults

The "creative brief implies serif" reflex is one of the most-tested tells. Serif is justified for genuinely editorial, luxury, publication, or heritage work where you can articulate why that specific serif fits that specific brand. It is not justified by the brief merely being creative.

`Fraunces` and `Instrument Serif` in particular are the two most over-selected display serifs and should not be default choices.

To emphasize a word inside a headline, use italic or bold of the **same** family. Injecting a serif word into a sans headline for visual interest is the amateur move.

When italic display type contains a descender (`y g j p q`), `leading-none` clips it. Use `leading-[1.1]` minimum plus a `pb-1` reserve on the wrapper.

### Color defaults

For premium-consumer briefs (cookware, wellness, artisan goods, luxury, heritage craft, DTC home) the reflex palette is warm beige plus brass plus espresso. These specific families are over-selected:

- Backgrounds: `#f5f1ea`, `#f7f5f1`, `#fbf8f1`, `#efeae0`, `#ece6db`, `#faf7f1`, `#e8dfcb`
- Accents: `#b08947`, `#b6553a`, `#9a2436`, `#9c6e2a`, `#bc7c3a`, `#7d5621`
- Text: `#1a1714`, `#1a1814`, `#1b1814`

The problem is not that the palette is ugly; it is that every generated premium-consumer site uses it, so the brand disappears. Rotate to a different family -- cold luxury (silver/chrome/smoke), forest (deep green/bone/amber), black and tan, cobalt and cream, terracotta and slate, or monochrome plus one saturated accent. It is acceptable when the brand brief actually names those colors.

Related to this, the "AI purple" gradient glow is the equivalent default for tech and SaaS briefs. Neutral base plus one high-contrast accent is the alternative. Purple is fine when the brand asks for it and it is executed with a consistent palette rather than as ambient gradient.
