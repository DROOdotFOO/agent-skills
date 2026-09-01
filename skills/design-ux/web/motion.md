---
title: Motion
impact: HIGH
impactDescription: Motion errors cause scroll jank, mobile frame drops, and accessibility failures that static review never catches
tags: motion, animation, scroll, gsap, framer-motion, reduced-motion, performance, choreography
---

# Motion

Motion is a communication tool, not decoration. Every animation costs frame budget, battery, and cognitive load. Adapted in part from `taste-skill` (MIT, see `THIRD-PARTY-NOTICES.md`).

## Motion Must Be Motivated

Before adding any animation, answer: what does this communicate? There are exactly four valid answers.

| Purpose            | Example                                            |
| ------------------ | -------------------------------------------------- |
| Hierarchy          | Drawing the eye to the primary action first        |
| Storytelling       | Revealing content in a sequence that matches a narrative |
| Feedback           | Acknowledging that a user action registered        |
| State transition   | Showing that something changed, and what           |

"It looked cool" is not on the list. If you cannot articulate the reason in one sentence, drop the animation. Animating everything because the library is installed is the most common failure.

Two corollaries:

- **Motion claimed is motion shown.** A page that promises movement must actually move (entry transition on the hero, scroll-reveal on key sections, hover feedback on primary actions). Half-built motion -- cut-off scroll triggers, jumpy enters, missing cleanups -- is worse than a clean static page. If you cannot ship working motion in the available scope, ship static.
- **Not every element needs a loop.** Infinite pulse/float/shimmer on every card is noise. Reserve perpetual motion for elements conveying live state (status indicators, active feeds).

## Never Drive Continuous Values Through React State

Continuous input -- scroll progress, pointer position, drag offset -- changes every frame. Routing it through `useState` re-renders the tree 60 times a second and collapses on mobile.

INCORRECT:

```tsx
// Re-renders the entire component tree on every scroll frame
export function Parallax({ children }: { children: React.ReactNode }) {
  const [scrollY, setScrollY] = useState(0);

  useEffect(() => {
    const onScroll = () => setScrollY(window.scrollY);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return <div style={{ transform: `translateY(${scrollY * 0.5}px)` }}>{children}</div>;
}
```

CORRECT:

```tsx
"use client";
import { motion, useScroll, useTransform, useReducedMotion } from "motion/react";

// Motion values live outside the React render cycle -- zero re-renders
export function Parallax({ children }: { children: React.ReactNode }) {
  const reduce = useReducedMotion();
  const { scrollYProgress } = useScroll();
  const y = useTransform(scrollYProgress, [0, 1], [0, 200]);

  if (reduce) return <div>{children}</div>;
  return <motion.div style={{ y }}>{children}</motion.div>;
}
```

Forbidden across the board:

- `window.addEventListener("scroll", ...)` -- fires every frame, no batching, jank-prone
- `window.scrollY` written into React state
- `requestAnimationFrame` loops that touch React state
- `useState` for mouse position, drag offset, or any magnetic/physics hover effect

Use instead: `useMotionValue` / `useTransform` / `useScroll`, `IntersectionObserver`, GSAP `ScrollTrigger`, or CSS scroll-driven animations (`animation-timeline: view()`).

## Animate Only Compositor Properties

`transform` and `opacity` are handled by the compositor and skip layout and paint. Everything else forces reflow.

INCORRECT:

```css
/* Triggers layout on every frame of the transition */
.panel {
  transition:
    width 0.3s ease,
    height 0.3s ease,
    top 0.3s ease,
    left 0.3s ease;
}
```

CORRECT:

```css
/* Compositor-only -- no layout, no paint */
.panel {
  transition:
    transform 0.3s ease,
    opacity 0.3s ease;
}

@media (prefers-reduced-motion: reduce) {
  .panel {
    transition: none;
  }
}
```

`will-change: transform` is a budget, not a hint -- apply it only to elements that are about to animate, and remove it after. Applying it broadly costs memory and can degrade the thing it was meant to help.

Grain and noise overlays go on a fixed, `pointer-events-none` pseudo-element (`fixed inset-0 pointer-events-none`), never on a scrolling container. A grain filter that repaints on scroll destroys mobile frame rate.

## Scroll Reveal: Prefer the Light Tool

Most "items appear as they enter the viewport" work needs no scroll library at all. Reach for pinning and scrubbing only when the effect genuinely requires them.

CORRECT (reveal without a scroll library):

```tsx
"use client";
import { motion, useReducedMotion } from "motion/react";

export function RevealStagger({ items }: { items: string[] }) {
  const reduce = useReducedMotion();
  return (
    <ul className="grid gap-6">
      {items.map((item, i) => (
        <motion.li
          key={item}
          initial={reduce ? false : { opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.6, delay: i * 0.06, ease: [0.16, 1, 0.3, 1] }}
        >
          {item}
        </motion.li>
      ))}
    </ul>
  );
}
```

The pure-CSS equivalent, when no animation library is present:

```css
@media (prefers-reduced-motion: no-preference) {
  .reveal {
    animation: reveal linear both;
    animation-timeline: view();
    animation-range: entry 0% entry 40%;
  }
}

@keyframes reveal {
  from {
    opacity: 0;
    transform: translateY(24px);
  }
}
```

Staggering: use `staggerChildren` (Motion) or `animation-delay: calc(var(--index) * 60ms)` (CSS). With `staggerChildren`, the parent holding `variants` and its children must be in the same client component tree, or the stagger silently does nothing.

## Pin-and-Scrub: The Failure Mode Is Always the Trigger Point

When an effect genuinely needs pinning (sticky card stack, horizontal pan), the recurring bug is the trigger firing before the section reaches the top of the viewport, so the user sees the animation already half-played.

INCORRECT:

```ts
// Animation starts while the section is still mid-viewport
ScrollTrigger.create({
  trigger: wrap.current,
  start: "top center", // or "top 80%" -- both wrong for pinned sections
  pin: true,
  scrub: 1,
});
```

CORRECT:

```tsx
"use client";
import { useRef, useEffect } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useReducedMotion } from "motion/react";

gsap.registerPlugin(ScrollTrigger);

export function HorizontalPan({ children }: { children: React.ReactNode }) {
  const wrap = useRef<HTMLDivElement>(null);
  const track = useRef<HTMLDivElement>(null);
  const reduce = useReducedMotion();

  useEffect(() => {
    if (reduce || !wrap.current || !track.current) return;
    const ctx = gsap.context(() => {
      const distance = track.current!.scrollWidth - window.innerWidth;
      gsap.to(track.current, {
        x: -distance,
        ease: "none",
        scrollTrigger: {
          trigger: wrap.current,
          start: "top top", // pin only once the section top hits the viewport top
          end: () => `+=${distance}`, // scroll length equals horizontal travel
          pin: true,
          scrub: 1,
          invalidateOnRefresh: true, // recompute on resize
        },
      });
    }, wrap);
    return () => ctx.revert(); // mandatory cleanup
  }, [reduce]);

  return (
    <section ref={wrap} className="relative overflow-hidden">
      <div ref={track} className="flex h-[100dvh] items-center">
        {children}
      </div>
    </section>
  );
}
```

The same `start: "top top"` plus `pin: true` rule applies to sticky card stacks. A "card stack on scroll" must actually pin and stack; a sequential fade-in list pretending to be a stack reads as broken.

Two structural requirements: wrap GSAP work in `gsap.context()` and return `ctx.revert()`, and isolate anything animated into a leaf component marked `"use client"`. Server components render static layout only.

## Reduced Motion Is Not Optional

Every non-trivial animation honors `prefers-reduced-motion`. Infinite loops, parallax, scroll hijacking, and pointer physics must collapse to static or instant, not merely slow down.

See `shared/accessibility.md` for the CSS-level contract and focus-visibility interaction. In component code the pattern is `useReducedMotion()` gating the animated branch, as shown above -- note `initial={reduce ? false : {...}}`, which skips the enter animation entirely rather than animating to the same place.

## Restraint Rules

- **One marquee per page maximum.** Two or more horizontal scrolling strips read as filler. Pick the section where it serves the content.
- **`layout` and `layoutId` are for real state changes** -- reordering lists, expanding modals, shared elements across routes. Wrapping static content in `layout` "for safety" costs measurement work every render.
- **Z-index is a system, not a reflex.** Reserve it for genuine stacking contexts (sticky header, modal, overlay, grain) and define the scale in one constants file. Scattered `z-10`/`z-50` guesses become unfixable.
