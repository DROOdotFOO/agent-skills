---
title: Devicons and Technology Icons
impact: LOW
impactDescription: Devicons enhance visual communication but are decorative; missing icons do not break functionality
tags: devicon, technology, logo, sprite, monochrome, duotone, svg-sprite, icon-set
---

# Devicons and Technology Icons

## Devicon Library

[Devicon](https://devicon.dev/) provides 700+ technology and developer tool icons in multiple styles. Available as SVG, font, or CDN.

### CDN Usage

```html
<!-- Full icon font (all icons, ~300 KB) -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/devicon.min.css">

<!-- Usage -->
<i class="devicon-react-original colored"></i>
<i class="devicon-typescript-plain"></i>
<i class="devicon-rust-original"></i>
```

### Selective SVG Import (Recommended)

INCORRECT:

```html
<!-- Loading entire icon font for 3 icons -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/devicon.min.css">
```

CORRECT:

```html
<!-- Download only the SVGs you need -->
<!-- https://github.com/devicons/devicon/tree/master/icons -->
<img src="/icons/react-original.svg" alt="React" width="32" height="32">
<img src="/icons/typescript-plain.svg" alt="TypeScript" width="32" height="32">
```

Or inline for styling control:

```html
<svg class="tech-icon" viewBox="0 0 128 128" width="32" height="32" aria-label="React">
  <!-- paste optimized SVG paths -->
</svg>
```

### Devicon Naming Convention

Pattern: `devicon-{name}-{style}` with optional `colored` class.

Styles: `plain`, `line`, `original`, `plain-wordmark`, `line-wordmark`, `original-wordmark`

```
devicon-react-original          # Default color
devicon-react-original colored  # Full brand colors
devicon-react-plain             # Simplified, single color
devicon-react-line              # Outline only
```

## Other Icon Sources

| Library          | Icons | Format   | License    | URL                                |
| ---------------- | ----- | -------- | ---------- | ---------------------------------- |
| Devicon          | 700+  | SVG/Font | MIT        | https://devicon.dev/               |
| Simple Icons     | 3000+ | SVG      | CC0        | https://simpleicons.org/           |
| Skill Icons      | 300+  | SVG      | MIT        | https://skillicons.dev/            |
| Lucide           | 1500+ | SVG      | ISC        | https://lucide.dev/                |
| Heroicons        | 300+  | SVG      | MIT        | https://heroicons.com/             |

For brand/technology logos: Simple Icons or Devicon.
For UI icons (arrows, menus, actions): Lucide or Heroicons.

## Converting Logos to Icon Sets

### From SVG Source

```bash
#!/usr/bin/env bash
set -euo pipefail

SVG_SOURCE="${1:?Usage: logo-to-icons.sh <source.svg>}"
NAME="${2:?Usage: logo-to-icons.sh <source.svg> <name>}"
OUT_DIR="${3:-.}"

mkdir -p "$OUT_DIR"

# Optimize SVG
npx svgo "$SVG_SOURCE" -o "$OUT_DIR/${NAME}.svg"

# Rasterize to PNG at standard sizes
for size in 16 24 32 48 64 128 256 512; do
  if command -v cairosvg &>/dev/null; then
    python3 -c "
import cairosvg
cairosvg.svg2png(url='${SVG_SOURCE}', write_to='${OUT_DIR}/${NAME}-${size}.png', output_width=${size}, output_height=${size})
"
  else
    convert -background none -density 300 "$SVG_SOURCE" -resize "${size}x${size}" "$OUT_DIR/${NAME}-${size}.png"
  fi
done

# Compress PNGs
if command -v pngquant &>/dev/null; then
  pngquant --quality=65-80 --skip-if-larger --ext .png --force "$OUT_DIR/${NAME}"-*.png
fi

echo "Generated icon set for ${NAME} in ${OUT_DIR}/"
```

### Monochrome Variants

For tech stacks and skill listings, monochrome icons ensure visual consistency.

```bash
# Convert colored SVG to monochrome (white on transparent)
sed 's/fill="[^"]*"/fill="currentColor"/g; s/style="[^"]*fill:[^;]*;/style="fill:currentColor;/g' \
  colored-icon.svg > mono-icon.svg
```

With ImageMagick:

```bash
# Rasterize then convert to single-color silhouette
convert input.png -colorspace Gray -threshold 50% -negate mono-icon.png
```

With sharp (Node):

```js
import sharp from "sharp";

async function toMonochrome(input: string, output: string, color = "#ffffff"): Promise<void> {
  await sharp(input)
    .ensureAlpha()
    .extractChannel("alpha")
    .toColourspace("b-w")
    .toFile(output);
}
```

## SVG Sprite Sheets

Bundle multiple SVG icons into a single sprite file for efficient loading.

### Building the Sprite

INCORRECT:

```html
<!-- 20 separate HTTP requests for 20 icons -->
<img src="/icons/react.svg">
<img src="/icons/typescript.svg">
<img src="/icons/rust.svg">
<!-- ... 17 more -->
```

CORRECT:

```xml
<!-- icons-sprite.svg -->
<svg xmlns="http://www.w3.org/2000/svg" style="display:none">
  <symbol id="icon-react" viewBox="0 0 128 128">
    <circle cx="64" cy="64" r="11.4"/>
    <ellipse cx="64" cy="64" rx="62" ry="24.6" fill="none" stroke="currentColor" stroke-width="5"/>
    <!-- ... paths -->
  </symbol>
  <symbol id="icon-typescript" viewBox="0 0 128 128">
    <!-- ... paths -->
  </symbol>
  <symbol id="icon-rust" viewBox="0 0 128 128">
    <!-- ... paths -->
  </symbol>
</svg>
```

### Using the Sprite

```html
<!-- Reference by fragment ID -->
<svg width="32" height="32" aria-label="React">
  <use href="/icons-sprite.svg#icon-react"/>
</svg>

<svg width="32" height="32" aria-label="TypeScript">
  <use href="/icons-sprite.svg#icon-typescript"/>
</svg>
```

### Generate Sprite from Directory (Node)

```js
import { readdirSync, readFileSync, writeFileSync } from "node:fs";
import { basename, join } from "node:path";

function buildSprite(iconDir: string, outputPath: string): void {
  const files = readdirSync(iconDir).filter((f) => f.endsWith(".svg"));
  const symbols = files.map((file) => {
    const id = `icon-${basename(file, ".svg")}`;
    const svg = readFileSync(join(iconDir, file), "utf8");

    // Extract viewBox from source SVG
    const viewBox = svg.match(/viewBox="([^"]+)"/)?.[1] ?? "0 0 128 128";

    // Extract inner content (strip outer <svg> tags)
    const inner = svg
      .replace(/<svg[^>]*>/, "")
      .replace(/<\/svg>/, "")
      .trim();

    return `  <symbol id="${id}" viewBox="${viewBox}">\n    ${inner}\n  </symbol>`;
  });

  const sprite = [
    '<svg xmlns="http://www.w3.org/2000/svg" style="display:none">',
    ...symbols,
    "</svg>",
  ].join("\n");

  writeFileSync(outputPath, sprite);
  console.log(`Built sprite with ${files.length} icons -> ${outputPath}`);
}
```

## Duotone Variants

Two-tone icons using CSS custom properties:

```css
.icon-duotone {
  --icon-primary: #6366f1;
  --icon-secondary: #818cf8;
  opacity: 0.85;
}
```

```xml
<svg viewBox="0 0 24 24">
  <!-- Background shape -->
  <path d="M3 3h18v18H3z" fill="var(--icon-secondary)" opacity="0.3"/>
  <!-- Foreground detail -->
  <path d="M12 6l6 6-6 6-6-6z" fill="var(--icon-primary)"/>
</svg>
```

## Tech Stack Badge Generators

For README and portfolio display:

```
<!-- shields.io with Simple Icons -->
![React](https://img.shields.io/badge/React-61DAFB?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white)
![Rust](https://img.shields.io/badge/Rust-000000?logo=rust&logoColor=white)
```

Using Skill Icons (visual grid):

```
<!-- Skill Icons API -->
![Tech Stack](https://skillicons.dev/icons?i=react,typescript,rust,python,go&theme=dark)
```
