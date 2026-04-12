---
title: Image Optimization
impact: HIGH
impactDescription: Unoptimized images are the largest contributor to page weight and poor Core Web Vitals
tags: svg, svgo, png, pngquant, optipng, webp, sharp, pillow, compression, format
---

# Image Optimization

## Format Selection Guide

| Format | Best for                          | Transparency | Animation | Browser support    |
| ------ | --------------------------------- | ------------ | --------- | ------------------ |
| SVG    | Logos, icons, illustrations       | Yes          | Yes (SMIL)| Universal          |
| PNG    | Screenshots, complex transparency | Yes          | No        | Universal          |
| WebP   | Photos, complex images            | Yes          | Yes       | 97%+ (2024)        |
| AVIF   | Photos (better than WebP)         | Yes          | Yes       | 93%+ (2024)        |
| ICO    | Favicons only                     | Yes          | No        | Universal          |
| JPEG   | Photos (no transparency needed)   | No           | No        | Universal          |

Decision tree:
1. Simple shapes, logos, icons? -> **SVG**
2. Needs transparency + universal support? -> **PNG** (optimize with pngquant)
3. Photo/complex image for modern browsers? -> **WebP** (with PNG/JPEG fallback)
4. Photo/complex for cutting-edge? -> **AVIF** (with WebP + JPEG fallback)
5. Favicon? -> **SVG** primary + **ICO** fallback

## SVG Optimization with SVGO

SVGO removes editor metadata, redundant attributes, and unused elements.

### CLI Usage

```bash
# Basic optimization
npx svgo input.svg -o output.svg

# Aggressive optimization (removes viewBox, title -- be careful)
npx svgo input.svg -o output.svg --multipass

# Process directory
npx svgo -f ./icons/ -o ./icons-optimized/

# Show savings
npx svgo input.svg -o output.svg --pretty --indent 2
```

### SVGO Config (svgo.config.js)

INCORRECT:

```js
// No config -- svgo defaults may remove accessibility attributes
// and collapse critical structure
```

CORRECT:

```js
// svgo.config.js
export default {
  multipass: true,
  plugins: [
    "preset-default",
    "removeDimensions",         // Use viewBox instead of width/height
    "sortAttrs",                // Consistent attribute order
    { name: "removeAttrs", params: { attrs: ["data-name", "class"] } },
    // Preserve accessibility
    { name: "removeTitle", active: false },
    { name: "removeDesc", active: false },
    // Preserve IDs used as CSS/JS targets
    { name: "cleanupIds", params: { preserve: ["logo", "icon"] } },
  ],
};
```

### Programmatic SVGO (Node)

```js
import { optimize } from "svgo";
import { readFileSync, writeFileSync } from "node:fs";

const svg = readFileSync("input.svg", "utf8");
const result = optimize(svg, {
  multipass: true,
  plugins: [
    "preset-default",
    "removeDimensions",
  ],
});
writeFileSync("output.svg", result.data);
console.log(`${svg.length} -> ${result.data.length} bytes (${Math.round((1 - result.data.length / svg.length) * 100)}% reduction)`);
```

## PNG Compression

### Lossless: optipng

Recompresses PNG with better DEFLATE settings. No quality loss.

```bash
# Moderate optimization (good speed/size tradeoff)
optipng -o2 image.png

# Maximum optimization (slow, best compression)
optipng -o7 image.png

# Process directory
find ./public -name '*.png' -exec optipng -o2 {} \;
```

### Lossy: pngquant

Reduces PNG to 8-bit palette. Dramatic size reduction (60-80%) with minimal visual impact for icons and UI elements.

INCORRECT:

```bash
# Overwrites without quality guard -- may produce visible banding
pngquant 64 image.png --force --ext .png
```

CORRECT:

```bash
# Quality range prevents visibly degraded output
pngquant --quality=65-80 --skip-if-larger --speed 1 --ext .png --force image.png

# Batch with quality guard
find ./public -name '*.png' -exec pngquant --quality=65-80 --skip-if-larger --ext .png --force {} \;
```

### Pipeline: optipng then pngquant

```bash
#!/usr/bin/env bash
set -euo pipefail

for png in "$@"; do
  original_size=$(stat -f%z "$png" 2>/dev/null || stat --format=%s "$png")
  optipng -o2 -quiet "$png"
  pngquant --quality=65-80 --skip-if-larger --ext .png --force "$png" 2>/dev/null || true
  new_size=$(stat -f%z "$png" 2>/dev/null || stat --format=%s "$png")
  saved=$((original_size - new_size))
  printf '%s: %d -> %d bytes (-%d)\n' "$png" "$original_size" "$new_size" "$saved"
done
```

## WebP Conversion

### With sharp (Node)

```js
import sharp from "sharp";

// PNG to WebP
await sharp("input.png")
  .webp({ quality: 80, effort: 6 })
  .toFile("output.webp");

// JPEG to WebP (lossy)
await sharp("photo.jpg")
  .webp({ quality: 75 })
  .toFile("photo.webp");

// PNG to WebP (lossless, for icons/screenshots)
await sharp("screenshot.png")
  .webp({ lossless: true })
  .toFile("screenshot.webp");
```

### With ImageMagick

```bash
convert input.png -quality 80 output.webp
convert photo.jpg -quality 75 photo.webp
```

### With Pillow (Python)

```python
from pathlib import Path
from PIL import Image

def to_webp(source: Path, quality: int = 80) -> Path:
    dest = source.with_suffix(".webp")
    img = Image.open(source)
    img.save(dest, "WEBP", quality=quality, method=6)
    return dest
```

## SVG to PNG with cairosvg (Python)

For rasterizing SVG to specific sizes:

```python
import cairosvg

# SVG to PNG at specific size
cairosvg.svg2png(
    url="logo.svg",
    write_to="logo-512.png",
    output_width=512,
    output_height=512,
)

# SVG string to PNG bytes
png_bytes = cairosvg.svg2png(
    bytestring=svg_content.encode(),
    output_width=192,
    output_height=192,
)
```

## Batch Processing Pipeline (Node)

```js
import sharp from "sharp";
import { globSync } from "node:fs";
import { basename, join } from "node:path";

async function optimizeDirectory(srcDir: string, outDir: string) {
  const files = globSync(`${srcDir}/**/*.{png,jpg,jpeg}`);

  for (const file of files) {
    const name = basename(file, ".png").replace(/\.jpe?g$/, "");

    // Optimized PNG
    await sharp(file)
      .png({ quality: 80, compressionLevel: 9 })
      .toFile(join(outDir, `${name}.png`));

    // WebP variant
    await sharp(file)
      .webp({ quality: 80, effort: 6 })
      .toFile(join(outDir, `${name}.webp`));

    // AVIF variant
    await sharp(file)
      .avif({ quality: 65, effort: 6 })
      .toFile(join(outDir, `${name}.avif`));
  }
}
```

## HTML: Serving Multiple Formats

```html
<picture>
  <source srcset="/hero.avif" type="image/avif">
  <source srcset="/hero.webp" type="image/webp">
  <img src="/hero.png" alt="Hero image" width="1200" height="630" loading="lazy">
</picture>
```

Always include `width` and `height` attributes to prevent layout shift (CLS).

## Size Budgets

Recommended maximums for web assets:

| Asset type          | Budget    | Notes                              |
| ------------------- | --------- | ---------------------------------- |
| Favicon SVG         | < 5 KB    | After SVGO                         |
| Favicon ICO         | < 15 KB   | Multi-size (16+32+48)              |
| App icon PNG (512)  | < 50 KB   | After pngquant                     |
| OG image            | < 300 KB  | JPEG/WebP at 1200x630              |
| Inline SVG icon     | < 2 KB    | Symbol sprite preferred for sets   |
| Hero image (WebP)   | < 200 KB  | With responsive srcset             |
