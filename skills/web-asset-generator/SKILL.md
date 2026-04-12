---
name: web-asset-generator
description: >
  Generate and optimize web assets: favicons, app icons, OG/social images, and
  devicons. TRIGGER when: user asks to create favicons, generate app icons (iOS,
  Android, PWA), build OG/social media images, optimize SVG/PNG/WebP, create icon
  sprite sheets, convert logos to icon sets, or work with devicons/technology icons.
  DO NOT TRIGGER when: user is designing UI layouts or component architecture
  (use design-ux skill), writing CSS/Tailwind styles (use droo-stack skill), or
  building image processing pipelines unrelated to web assets.
metadata:
  author: DROOdotFOO
  version: "1.0.0"
  tags: favicon, icons, og-image, social, devicons, svg, png, webp, pwa, optimization
---

# web-asset-generator

Generate production-ready icon sets, social images, and optimized assets from source images. One source file in, every platform-specific variant out.

## What You Get

- Favicon generation (ICO, PNG, SVG) for all browsers and sizes
- Apple touch icons, Android adaptive icons, PWA manifest icons
- OG/social media images with proper dimensions and metadata tags
- Devicon integration and custom technology icon creation
- Image optimization pipelines (SVGO, pngquant, sharp, WebP)
- Format selection guidance (when to use SVG vs PNG vs WebP vs ICO)

## When to Use

- Generating favicon sets from a source logo or SVG
- Creating iOS/Android/PWA app icon variants
- Building OG images and Twitter card assets
- Converting logos into lightweight icon sets
- Optimizing SVG files (removing editor cruft, minifying)
- Compressing PNGs or converting to WebP
- Creating devicon/technology icon sprites

## When NOT to Use

- **UI layout and component design** -- use `design-ux`
- **CSS/Tailwind styling patterns** -- use `droo-stack`
- **General image editing** (photo manipulation, filters) -- not a skill concern
- **Video or animation assets** -- out of scope

## Reading Guide

| Working on                                   | Read                     |
| -------------------------------------------- | ------------------------ |
| Favicons, Apple touch, Android, PWA manifest | `favicon-and-icons.md`   |
| SVG cleanup, PNG crush, WebP, format choice  | `image-optimization.md`  |
| OG tags, Twitter cards, social dimensions    | `social-images.md`       |
| Devicon libraries, logo sprites, monochrome  | `devicons.md`            |

## See also

- `design-ux` -- for design token systems, color palettes, and accessibility
- `droo-stack` -- for code-level patterns in TypeScript, Python, and shell

## Tool Landscape

| Tool                    | Language | Use case                             |
| ----------------------- | -------- | ------------------------------------ |
| sharp                   | Node     | Resize, convert, compress images     |
| svgo                    | Node     | SVG optimization and cleanup         |
| imagemagick (convert)   | CLI      | Format conversion, ICO generation    |
| optipng                 | CLI      | Lossless PNG optimization            |
| pngquant                | CLI      | Lossy PNG compression (8-bit)        |
| real-favicon-generator  | Web/CLI  | Full favicon package from one image  |
| pwa-asset-generator     | Node     | PWA splash screens and icons         |
| Pillow                  | Python   | Programmatic image generation        |
| cairosvg                | Python   | SVG to PNG/PDF rasterization         |

## Common Pitfalls

| Mistake                                  | Why It Fails                                       | Better Approach                              |
| ---------------------------------------- | -------------------------------------------------- | -------------------------------------------- |
| Single favicon.ico only                  | Missing Apple touch, Android, PWA                  | Generate full set: ICO + PNG + SVG + manifest |
| Huge unoptimized PNG favicons            | Slow page load, poor Lighthouse score              | Compress with pngquant, serve SVG where able |
| OG image wrong dimensions               | Gets cropped or letterboxed on social platforms    | Use 1200x630 for OG, 1200x675 for Twitter   |
| SVG with embedded raster images          | Defeats SVG purpose, huge file size                | Trace rasters to paths or use PNG instead    |
| No maskable icon for Android             | Icon looks tiny in adaptive icon circle            | Add `"purpose": "maskable"` variant to manifest |
| Serving WebP without PNG fallback        | Breaks Safari <14, older browsers                  | Use `<picture>` element with PNG fallback    |

## Key Conventions

- **Source-first**: Always keep the highest-resolution source file; generate variants from it
- **Automate generation**: Script the conversion pipeline; never hand-resize icons
- **Format-appropriate**: SVG for simple logos, PNG for complex/photographic, WebP for modern browsers
- **Manifest-complete**: PWA manifest must include all required icon sizes with correct `purpose` fields
- **Lossless then lossy**: Run lossless optimization first (optipng/svgo), then lossy (pngquant) if size still matters
