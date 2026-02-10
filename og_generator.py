#!/usr/bin/env python3
"""
Kwalia Essay OG Image Generator
Generates 1200x630 social cards for essay preview cards (Telegram, Twitter, etc.).

Brand specs (STYLE_GUIDE.md):
  Colors: #FFFF00 yellow, #474747 gray, #FF70A6 pink, #FFFFFF white
  Fonts:  Instrument Serif (titles), Plus Jakarta Sans (body)

Design rules:
  - White background, thin pink strip on the left edge
  - Geometric shapes in brand colors at low opacity
  - Each card uses only TWO of three shape types (circles, triangles, squares)
  - All three brand accent colors (pink, yellow, gray) can appear
  - Composition is deterministic: same slug always produces the same image

Usage:
  # Single image
  python og_generator.py --title "Essay Title" --subtitle "Subtitle" --slug "essay-slug" --output ./og/essay-slug.jpg

  # Batch from essays.json
  python og_generator.py --batch data/essays.json --output-dir assets/og/

  # Generate for a specific language
  python og_generator.py --batch data/essays.json --output-dir assets/og/ --lang es

Environment:
  KWALIA_FONT_DIR  Path to font directory (default: fonts/ relative to script)
"""

import argparse
import hashlib
import json
import math
import os
import sys
from PIL import Image, ImageDraw, ImageFont

# ─── BRAND COLORS ───
COLORS = {
    'white':  (255, 255, 255),
    'yellow': (255, 255, 0),      # #FFFF00
    'pink':   (255, 112, 166),    # #FF70A6
    'gray':   (71, 71, 71),       # #474747
}

ACCENT_COLORS = ['pink', 'yellow', 'gray']
SHAPE_TYPES = ['circle', 'triangle', 'square']

# ─── FONTS ───
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.environ.get("KWALIA_FONT_DIR", os.path.join(SCRIPT_DIR, "fonts"))

# Map to actual font files. Adjust filenames if your repo uses different names.
FONT_PATHS = {
    'title':    "InstrumentSerif-Italic.ttf",
    'subtitle': "PlusJakartaSans-Light.ttf",
    'brand':    "PlusJakartaSans-Medium.ttf",
    'category': "PlusJakartaSans-Regular.ttf",
}

# ─── CANVAS ───
WIDTH  = 1200
HEIGHT = 630
PINK_STRIP_W = 8
TEXT_LEFT = 56
TEXT_RIGHT = WIDTH - 56
TEXT_AREA_W = TEXT_RIGHT - TEXT_LEFT


# ─── HELPERS ───

def load_font(key, size):
    """Load a font by key, with fallback to default."""
    path = os.path.join(FONT_DIR, FONT_PATHS[key])
    if os.path.exists(path):
        return ImageFont.truetype(path, size)
    # Try common alternative paths
    alt_paths = {
        'title':    ["Instrument_Serif/InstrumentSerif-Italic.ttf"],
        'subtitle': ["Plus_Jakarta_Sans/static/PlusJakartaSans-Light.ttf",
                      "Plus_Jakarta_Sans/PlusJakartaSans-Light.ttf"],
        'brand':    ["Plus_Jakarta_Sans/static/PlusJakartaSans-Medium.ttf",
                      "Plus_Jakarta_Sans/PlusJakartaSans-Medium.ttf"],
        'category': ["Plus_Jakarta_Sans/static/PlusJakartaSans-Regular.ttf",
                      "Plus_Jakarta_Sans/PlusJakartaSans-Regular.ttf"],
    }
    for alt in alt_paths.get(key, []):
        alt_full = os.path.join(FONT_DIR, alt)
        if os.path.exists(alt_full):
            return ImageFont.truetype(alt_full, size)
    print(f"  ⚠ Font not found for '{key}' at {path}, using default", file=sys.stderr)
    return ImageFont.load_default()


def seeded_floats(seed_str, n=40):
    """Deterministic pseudo-random floats from a string seed."""
    h = hashlib.sha256(seed_str.encode()).hexdigest()
    values = []
    while len(values) < n:
        for i in range(0, len(h) - 1, 2):
            if len(values) >= n:
                break
            values.append(int(h[i:i+2], 16) / 255.0)
        h = hashlib.sha256(h.encode()).hexdigest()
    return values


def pick_two_shapes(slug):
    """Deterministically pick 2 of 3 shape types for this essay."""
    h = hashlib.md5(slug.encode()).hexdigest()
    exclude = int(h[:2], 16) % 3
    return [s for i, s in enumerate(SHAPE_TYPES) if i != exclude]


def make_overlay():
    return Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))


def draw_circle(cx, cy, r, color_rgba):
    overlay = make_overlay()
    ImageDraw.Draw(overlay).ellipse(
        [cx - r, cy - r, cx + r, cy + r], fill=color_rgba)
    return overlay


def draw_triangle(cx, cy, size, rotation, color_rgba):
    overlay = make_overlay()
    points = [(cx + size * math.cos(rotation + i * 2 * math.pi / 3),
               cy + size * math.sin(rotation + i * 2 * math.pi / 3))
              for i in range(3)]
    ImageDraw.Draw(overlay).polygon(points, fill=color_rgba)
    return overlay


def draw_square(cx, cy, size, rotation, color_rgba):
    overlay = make_overlay()
    points = [(cx + size * math.cos(rotation + i * math.pi / 2),
               cy + size * math.sin(rotation + i * math.pi / 2))
              for i in range(4)]
    ImageDraw.Draw(overlay).polygon(points, fill=color_rgba)
    return overlay


SHAPE_DRAWERS = {
    'circle':   lambda cx, cy, size, rot, col: draw_circle(cx, cy, size, col),
    'triangle': lambda cx, cy, size, rot, col: draw_triangle(cx, cy, size, rot, col),
    'square':   lambda cx, cy, size, rot, col: draw_square(cx, cy, size, rot, col),
}


def generate_shapes(img, slug):
    """Add deterministic geometric shapes. Two shape types, all accent colors."""
    vals = seeded_floats(slug, 50)
    vi = 0
    def v():
        nonlocal vi
        r = vals[vi % len(vals)]
        vi += 1
        return r

    two_shapes = pick_two_shapes(slug)
    num_shapes = 3 + int(v() * 3)  # 3-5 shapes

    for _ in range(num_shapes):
        shape_name = two_shapes[min(int(v() * len(two_shapes)), len(two_shapes) - 1)]
        color_name = ACCENT_COLORS[min(int(v() * len(ACCENT_COLORS)), len(ACCENT_COLORS) - 1)]
        base_color = COLORS[color_name]

        if color_name == 'gray':
            alpha = int(15 + v() * 35)   # 15-50
        else:
            alpha = int(25 + v() * 65)   # 25-90

        color_rgba = (*base_color, alpha)
        cx = int(40 + v() * (WIDTH - 80))
        cy = int(40 + v() * (HEIGHT - 80))
        size = int(25 + v() * 95)  # 25-120px
        rotation = v() * 2 * math.pi

        drawer = SHAPE_DRAWERS[shape_name]
        overlay = drawer(cx, cy, size, rotation, color_rgba)
        img = Image.alpha_composite(img, overlay)

    return img


def wrap_text(text, font, max_width, draw):
    """Word-wrap text to fit within max_width pixels."""
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def generate_og_image(title, subtitle, slug, output_path, category=""):
    """Generate a single 1200x630 OG image."""

    img = Image.new('RGBA', (WIDTH, HEIGHT), (*COLORS['white'], 255))
    img = generate_shapes(img, slug)
    draw = ImageDraw.Draw(img)

    # Pink strip on the left
    draw.rectangle([0, 0, PINK_STRIP_W, HEIGHT], fill=(*COLORS['pink'], 255))

    # Fonts
    font_title    = load_font('title', 48)
    font_subtitle = load_font('subtitle', 20)
    font_brand    = load_font('brand', 15)
    font_category = load_font('category', 13)

    # ── Title ──
    title_lines = wrap_text(title, font_title, TEXT_AREA_W, draw)
    line_h = 60
    block_h = len(title_lines) * line_h
    title_y = max(70, int((HEIGHT - block_h - 80) * 0.35))

    for i, line in enumerate(title_lines):
        y = title_y + i * line_h
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            draw.text((TEXT_LEFT + dx, y + dy), line,
                      font=font_title, fill=(255, 255, 255, 160))
        draw.text((TEXT_LEFT, y), line,
                  font=font_title, fill=(*COLORS['gray'], 255))

    # ── Subtitle ──
    if subtitle:
        sub_y = title_y + block_h + 20
        for i, line in enumerate(wrap_text(subtitle, font_subtitle, TEXT_AREA_W, draw)):
            draw.text((TEXT_LEFT, sub_y + i * 28), line,
                      font=font_subtitle, fill=(120, 120, 120, 230))

    # ── Brand (bottom right) ──
    bbox = draw.textbbox((0, 0), "kwalia.ai", font=font_brand)
    draw.text((TEXT_RIGHT - (bbox[2] - bbox[0]), HEIGHT - 44), "kwalia.ai",
              font=font_brand, fill=(*COLORS['gray'], 200))

    # ── Category (bottom left) ──
    if category:
        draw.text((TEXT_LEFT, HEIGHT - 42), category.upper(),
                  font=font_category, fill=(120, 120, 120, 200))

    # Save as RGB JPEG
    final = Image.new('RGB', (WIDTH, HEIGHT), COLORS['white'])
    final.paste(img, mask=img.split()[3])
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    final.save(output_path, 'JPEG', quality=92)
    return output_path


def batch_from_json(json_path, output_dir, lang="en"):
    """Generate OG images for all essays in essays.json."""
    os.makedirs(output_dir, exist_ok=True)
    with open(json_path) as f:
        essays = json.load(f)

    count = 0
    for essay in essays:
        slug_obj = essay.get("slug", {})
        slug = slug_obj.get(lang, slug_obj.get("en", essay.get("id", "unknown")))
        title = essay.get("title", {}).get(lang, essay.get("title", {}).get("en", "Untitled"))
        subtitle = essay.get("subtitle", {}).get(lang, essay.get("subtitle", {}).get("en", ""))
        topics = essay.get("tmmTopics", [])
        category = topics[0].replace("-", " ").title() if topics else ""

        path = os.path.join(output_dir, f"{slug}.jpg")
        generate_og_image(title, subtitle, slug, path, category)
        count += 1
        print(f"  ✓ {slug}.jpg")

    print(f"\nGenerated {count} images in {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Kwalia OG Image Generator")
    parser.add_argument("--title", help="Essay title (single mode)")
    parser.add_argument("--subtitle", default="", help="Essay subtitle (single mode)")
    parser.add_argument("--slug", help="Essay slug (single mode)")
    parser.add_argument("--category", default="", help="Category label (single mode)")
    parser.add_argument("--output", help="Output file path (single mode)")
    parser.add_argument("--batch", help="Path to essays.json (batch mode)")
    parser.add_argument("--output-dir", default="assets/og", help="Output directory (batch mode)")
    parser.add_argument("--lang", default="en", choices=["en", "es"], help="Language for batch mode")
    args = parser.parse_args()

    if args.batch:
        batch_from_json(args.batch, args.output_dir, args.lang)
    elif args.title and args.slug:
        out = args.output or f"{args.slug}.jpg"
        generate_og_image(args.title, args.subtitle, args.slug, out, args.category)
        print(f"Generated: {out}")
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
