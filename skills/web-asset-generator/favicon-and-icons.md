---
title: Favicons and App Icons
impact: HIGH
impactDescription: Missing or broken favicons/icons cause poor branding, PWA install failures, and bad search appearance
tags: favicon, ico, png, svg, apple-touch, android, pwa, manifest, windows-tile
---

# Favicons and App Icons

## Required Favicon Set

Modern browsers need multiple favicon formats. The minimum viable set:

| File                       | Size        | Purpose                        |
| -------------------------- | ----------- | ------------------------------ |
| `favicon.ico`              | 16x16+32x32 | Legacy browsers, bookmarks    |
| `favicon.svg`              | scalable    | Modern browsers (dark mode!)   |
| `favicon-16x16.png`        | 16x16       | Browser tabs                   |
| `favicon-32x32.png`        | 32x32       | Browser tabs (HiDPI)           |
| `apple-touch-icon.png`     | 180x180     | iOS home screen                |
| `android-chrome-192x192.png` | 192x192   | Android home screen            |
| `android-chrome-512x512.png` | 512x512   | Android splash screen          |
| `mstile-150x150.png`       | 150x150     | Windows tiles                  |

## HTML Head Tags

INCORRECT:

```html
<!-- Single favicon, no Apple/Android/manifest support -->
<link rel="icon" href="/favicon.ico">
```

CORRECT:

```html
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<meta name="theme-color" content="#1a1b2e">
```

## SVG Favicon with Dark Mode Support

SVG favicons can adapt to the user's color scheme:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <style>
    rect { fill: #6366f1; }
    @media (prefers-color-scheme: dark) {
      rect { fill: #818cf8; }
    }
  </style>
  <rect width="32" height="32" rx="4"/>
  <text x="16" y="22" text-anchor="middle" fill="white"
        font-family="monospace" font-size="18" font-weight="bold">A</text>
</svg>
```

## Generate Favicons with ImageMagick

From a source PNG (512x512 or larger):

```bash
# Generate ICO (multi-size)
convert source-512.png \
  \( -clone 0 -resize 16x16 \) \
  \( -clone 0 -resize 32x32 \) \
  \( -clone 0 -resize 48x48 \) \
  -delete 0 favicon.ico

# Generate PNG variants
convert source-512.png -resize 16x16   favicon-16x16.png
convert source-512.png -resize 32x32   favicon-32x32.png
convert source-512.png -resize 180x180 apple-touch-icon.png
convert source-512.png -resize 192x192 android-chrome-192x192.png
# 512x512 keep as-is for splash
cp source-512.png android-chrome-512x512.png
convert source-512.png -resize 150x150 mstile-150x150.png
```

## Generate Favicons with Sharp (Node)

```js
import sharp from "sharp";

const sizes = [
  { name: "favicon-16x16.png", size: 16 },
  { name: "favicon-32x32.png", size: 32 },
  { name: "apple-touch-icon.png", size: 180 },
  { name: "android-chrome-192x192.png", size: 192 },
  { name: "android-chrome-512x512.png", size: 512 },
  { name: "mstile-150x150.png", size: 150 },
];

async function generateFavicons(source: string, outDir: string) {
  for (const { name, size } of sizes) {
    await sharp(source)
      .resize(size, size, { fit: "contain", background: { r: 0, g: 0, b: 0, alpha: 0 } })
      .png()
      .toFile(`${outDir}/${name}`);
  }
}
```

## Generate Favicons with Pillow (Python)

```python
from pathlib import Path
from PIL import Image

SIZES = {
    "favicon-16x16.png": 16,
    "favicon-32x32.png": 32,
    "apple-touch-icon.png": 180,
    "android-chrome-192x192.png": 192,
    "android-chrome-512x512.png": 512,
    "mstile-150x150.png": 150,
}

def generate_favicons(source: Path, out_dir: Path) -> None:
    img = Image.open(source)
    out_dir.mkdir(parents=True, exist_ok=True)

    for name, size in SIZES.items():
        resized = img.resize((size, size), Image.LANCZOS)
        resized.save(out_dir / name, optimize=True)

    # Generate multi-size ICO
    img.save(
        out_dir / "favicon.ico",
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48)],
    )
```

## PWA Web App Manifest

INCORRECT:

```json
{
  "icons": [
    { "src": "/icon-192.png", "sizes": "192x192" }
  ]
}
```

CORRECT:

```json
{
  "name": "My App",
  "short_name": "App",
  "icons": [
    { "src": "/android-chrome-192x192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/android-chrome-512x512.png", "sizes": "512x512", "type": "image/png" },
    { "src": "/maskable-icon-512x512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ],
  "theme_color": "#1a1b2e",
  "background_color": "#1a1b2e",
  "display": "standalone"
}
```

The `maskable` icon needs extra safe-zone padding (inner 80% circle). Design the logo within the center 80% of the canvas.

## Android Adaptive Icons

Android adaptive icons use two layers: foreground and background. The system applies masks (circle, squircle, rounded square) per device.

```bash
# Generate maskable icon: logo centered in inner 80%
convert -size 512x512 xc:"#1a1b2e" \
  \( logo.png -resize 410x410 -gravity center \) \
  -composite maskable-icon-512x512.png
```

The safe zone is a circle with diameter = 80% of icon size (409.6px for 512x512). Keep all important content inside this zone.

## iOS Icon Requirements

| Size    | Scale | File                   | Usage              |
| ------- | ----- | ---------------------- | ------------------ |
| 180x180 | 3x    | apple-touch-icon.png   | iPhone home screen |
| 167x167 | 2x    | icon-167.png           | iPad Pro           |
| 152x152 | 2x    | icon-152.png           | iPad               |
| 120x120 | 2x/3x | icon-120.png           | iPhone (older)     |
| 1024x1024 | 1x  | icon-1024.png          | App Store          |

Apple touch icons should NOT have transparency -- iOS fills transparent areas with black. Use a solid background color.

INCORRECT:

```bash
# Transparent background -- will render with black fill on iOS
convert logo.png -resize 180x180 apple-touch-icon.png
```

CORRECT:

```bash
# Solid background, then composite logo
convert -size 180x180 xc:"#1a1b2e" \
  \( logo.png -resize 140x140 -gravity center \) \
  -composite apple-touch-icon.png
```

## pwa-asset-generator

Generates all iOS splash screens and icons from a single source:

```bash
npx pwa-asset-generator logo.svg ./assets \
  --background "#1a1b2e" \
  --splash-only false \
  --icon-only false \
  --type png \
  --padding "10%"
```

Outputs HTML link tags and manifest JSON ready to paste.

## real-favicon-generator CLI

```bash
npx real-favicon-generator \
  --input logo.svg \
  --output ./public \
  --settings '{"favicon": {"desktop_browser": {}, "ios": {"picture_aspect": "background_and_margin", "margin": "14%", "background_color": "#1a1b2e"}, "android_chrome": {"picture_aspect": "shadow", "manifest": {"name": "App", "display": "standalone"}}}}'
```

## Shell Script: Full Pipeline

```bash
#!/usr/bin/env bash
set -euo pipefail

SOURCE="${1:?Usage: generate-icons.sh <source.png>}"
OUT_DIR="${2:-./public}"

mkdir -p "$OUT_DIR"

# PNG variants
for size in 16 32 48 150 152 167 180 192 512 1024; do
  convert "$SOURCE" -resize "${size}x${size}" "$OUT_DIR/icon-${size}x${size}.png"
done

# Named aliases
cp "$OUT_DIR/icon-180x180.png" "$OUT_DIR/apple-touch-icon.png"
cp "$OUT_DIR/icon-192x192.png" "$OUT_DIR/android-chrome-192x192.png"
cp "$OUT_DIR/icon-512x512.png" "$OUT_DIR/android-chrome-512x512.png"
cp "$OUT_DIR/icon-150x150.png" "$OUT_DIR/mstile-150x150.png"

# Multi-size ICO
convert "$SOURCE" \
  \( -clone 0 -resize 16x16 \) \
  \( -clone 0 -resize 32x32 \) \
  \( -clone 0 -resize 48x48 \) \
  -delete 0 "$OUT_DIR/favicon.ico"

# Optimize PNGs
if command -v pngquant &>/dev/null; then
  pngquant --quality=65-80 --skip-if-larger --ext .png --force "$OUT_DIR"/*.png
fi

echo "Generated $(ls "$OUT_DIR"/*.png "$OUT_DIR"/*.ico | wc -l) icon files"
```
