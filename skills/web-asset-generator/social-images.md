---
title: Social and OG Images
impact: MEDIUM
impactDescription: Wrong OG images cause poor link previews on social platforms but do not break functionality
tags: og, open-graph, twitter-card, social, meta, dimensions, template, seo
---

# Social and OG Images

## Platform Dimensions

| Platform           | Type              | Size (px)  | Aspect ratio | Format      |
| ------------------ | ----------------- | ---------- | ------------ | ----------- |
| Open Graph (FB)    | og:image          | 1200x630   | 1.91:1       | JPEG/PNG    |
| Twitter/X          | summary_large     | 1200x675   | 16:9         | JPEG/PNG    |
| Twitter/X          | summary (small)   | 240x240    | 1:1          | JPEG/PNG    |
| LinkedIn           | share             | 1200x627   | 1.91:1       | JPEG/PNG    |
| Discord            | embed             | 1200x630   | 1.91:1       | JPEG/PNG    |
| Slack              | unfurl            | 1200x630   | 1.91:1       | JPEG/PNG    |
| Pinterest          | pin               | 1000x1500  | 2:3          | JPEG/PNG    |
| WhatsApp           | link preview      | 300x200    | 3:2          | JPEG/PNG    |

The safe default: **1200x630** covers Open Graph, LinkedIn, Discord, and Slack. Add a 1200x675 variant for Twitter/X `summary_large_image`.

## HTML Meta Tags

INCORRECT:

```html
<!-- Missing og:image dimensions, no Twitter card, relative URL -->
<meta property="og:image" content="/images/share.png">
```

CORRECT:

```html
<!-- Open Graph -->
<meta property="og:title" content="Page Title">
<meta property="og:description" content="Brief description under 200 chars">
<meta property="og:image" content="https://example.com/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:type" content="image/png">
<meta property="og:image:alt" content="Descriptive alt text for the image">
<meta property="og:url" content="https://example.com/page">
<meta property="og:type" content="website">

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Page Title">
<meta name="twitter:description" content="Brief description">
<meta name="twitter:image" content="https://example.com/twitter-card.png">
<meta name="twitter:image:alt" content="Descriptive alt text">
```

Key rules:
- `og:image` URL must be **absolute** (full https:// URL)
- Include `og:image:width` and `og:image:height` for faster rendering
- `og:image:alt` is required for accessibility
- Twitter falls back to OG tags, but `twitter:card` must be explicit
- Image file size should be under 5 MB (Facebook), ideally under 300 KB

## Generate OG Image with Sharp (Node)

```js
import sharp from "sharp";

async function generateOgImage(
  backgroundPath: string,
  title: string,
  outPath: string,
): Promise<void> {
  // Create SVG text overlay
  const svgText = `
    <svg width="1200" height="630" xmlns="http://www.w3.org/2000/svg">
      <style>
        .title { fill: white; font-family: sans-serif; font-size: 64px; font-weight: bold; }
        .subtitle { fill: #a0a0a0; font-family: sans-serif; font-size: 28px; }
      </style>
      <text x="80" y="320" class="title">${escapeXml(title)}</text>
      <text x="80" y="380" class="subtitle">example.com</text>
    </svg>`;

  await sharp(backgroundPath)
    .resize(1200, 630, { fit: "cover" })
    .composite([{ input: Buffer.from(svgText), top: 0, left: 0 }])
    .jpeg({ quality: 85 })
    .toFile(outPath);
}

function escapeXml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
```

## Generate OG Image with Pillow (Python)

```python
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def generate_og_image(
    title: str,
    output: Path,
    bg_color: str = "#1a1b2e",
    text_color: str = "#ffffff",
    width: int = 1200,
    height: int = 630,
) -> None:
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Use a system font or bundle your own
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 64)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
    except OSError:
        font = ImageFont.load_default()
        small_font = font

    # Word-wrap title
    words = title.split()
    lines: list[str] = []
    current_line = ""
    for word in words:
        test = f"{current_line} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] > width - 160:
            lines.append(current_line)
            current_line = word
        else:
            current_line = test
    lines.append(current_line)

    # Draw text
    y = height // 2 - len(lines) * 40
    for line in lines:
        draw.text((80, y), line, fill=text_color, font=font)
        y += 80

    # Domain watermark
    draw.text((80, height - 80), "example.com", fill="#808080", font=small_font)

    img.save(output, "PNG", optimize=True)
```

## Dynamic OG Images (Next.js / Vercel)

Next.js can generate OG images at the edge using `@vercel/og`:

```tsx
// app/og/route.tsx
import { ImageResponse } from "next/og";

export const runtime = "edge";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const title = searchParams.get("title") ?? "Default Title";

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "80px",
          backgroundColor: "#1a1b2e",
          color: "white",
          fontFamily: "sans-serif",
        }}
      >
        <div style={{ fontSize: 64, fontWeight: "bold" }}>{title}</div>
        <div style={{ fontSize: 28, color: "#808080", marginTop: 20 }}>example.com</div>
      </div>
    ),
    { width: 1200, height: 630 },
  );
}
```

Reference in page metadata:

```tsx
export const metadata = {
  openGraph: {
    images: [{ url: "/og?title=My+Page", width: 1200, height: 630 }],
  },
};
```

## Validation and Debugging

Test OG tags before deploying:

| Tool                                    | URL                                          |
| --------------------------------------- | -------------------------------------------- |
| Facebook Sharing Debugger              | https://developers.facebook.com/tools/debug/ |
| Twitter Card Validator                 | https://cards-dev.twitter.com/validator       |
| LinkedIn Post Inspector                | https://www.linkedin.com/post-inspector/      |
| opengraph.xyz (preview all platforms)  | https://www.opengraph.xyz/                    |

Common issues:
- **Image not showing**: URL is relative (must be absolute https://)
- **Old image cached**: Use Facebook debugger "Scrape Again" button
- **Image cropped**: Wrong dimensions for the platform
- **No image on first share**: Crawlers time out; pre-render or cache-warm the OG image URL

## Checklist

- [ ] `og:image` URL is absolute (https://)
- [ ] Image is 1200x630 pixels minimum
- [ ] File size under 300 KB (under 5 MB hard limit)
- [ ] `og:image:width` and `og:image:height` specified
- [ ] `og:image:alt` present for accessibility
- [ ] `twitter:card` set to `summary_large_image`
- [ ] Tested with Facebook debugger and Twitter validator
- [ ] No text in the outer 10% margins (gets clipped on some platforms)
