#!/usr/bin/env python3
"""
Update OG meta tags in essay HTML files to use generated OG images.

Usage:
  python update_og_tags.py                           # Update all essays
  python update_og_tags.py essays/my-essay.html      # Update specific file
"""

import json
import os
import re
import sys

ESSAYS_DIR = "essays"
DATA_FILE = "data/essays.json"
BASE_URL = "https://kwalia.ai"


def load_essays_json():
    """Load essays metadata."""
    with open(DATA_FILE) as f:
        return json.load(f)


def get_essay_metadata(slug, essays_data):
    """Find essay metadata by slug (checks both en and es slugs)."""
    for essay in essays_data:
        slug_obj = essay.get("slug", {})
        if slug_obj.get("en") == slug:
            return essay, "en"
        if slug_obj.get("es") == slug:
            return essay, "es"
    return None, None


def update_og_tags(html_path, essays_data):
    """Update OG tags in a single HTML file."""
    filename = os.path.basename(html_path)
    slug = filename.replace(".html", "")

    essay, lang = get_essay_metadata(slug, essays_data)
    if not essay:
        return False, f"No metadata found for {slug}"

    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Get title and subtitle for this language
    title = essay.get("title", {}).get(lang, "Untitled")
    subtitle = essay.get("subtitle", {}).get(lang, "")
    excerpt = essay.get("excerpt", {}).get(lang, subtitle)

    og_image_url = f"{BASE_URL}/assets/og/{slug}.jpg"
    essay_url = f"{BASE_URL}/essays/{slug}"

    # Patterns to match existing OG tags
    replacements = [
        (r'<meta property="og:image" content="[^"]*"[^>]*>',
         f'<meta property="og:image" content="{og_image_url}">'),
        (r'<meta property="og:image:width" content="[^"]*"[^>]*>',
         ''),  # Remove old, will add new
        (r'<meta property="og:image:height" content="[^"]*"[^>]*>',
         ''),  # Remove old, will add new
        (r'<meta name="twitter:image" content="[^"]*"[^>]*>',
         f'<meta name="twitter:image" content="{og_image_url}">'),
    ]

    modified = content
    for pattern, replacement in replacements:
        modified = re.sub(pattern, replacement, modified)

    # Check if og:image exists, if not add all OG tags after og:type or after </title>
    if '<meta property="og:image"' not in modified:
        og_block = f'''<meta property="og:image" content="{og_image_url}">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta name="twitter:image" content="{og_image_url}">'''

        # Insert after og:type if exists, else after </title>
        if '<meta property="og:type"' in modified:
            modified = re.sub(
                r'(<meta property="og:type" content="[^"]*"[^>]*>)',
                r'\1\n    ' + og_block,
                modified
            )
        elif '</title>' in modified:
            modified = modified.replace('</title>', f'</title>\n    {og_block}')
    else:
        # Add image dimensions after og:image if not present
        if '<meta property="og:image:width"' not in modified:
            modified = re.sub(
                r'(<meta property="og:image" content="[^"]*"[^>]*>)',
                r'\1\n    <meta property="og:image:width" content="1200">\n    <meta property="og:image:height" content="630">',
                modified
            )

    # Add twitter:image if not present
    if '<meta name="twitter:image"' not in modified:
        modified = re.sub(
            r'(<meta name="twitter:card" content="[^"]*"[^>]*>)',
            r'\1\n    <meta name="twitter:image" content="' + og_image_url + '">',
            modified
        )

    # Clean up empty lines from removed tags
    modified = re.sub(r'\n\s*\n\s*\n', '\n\n', modified)

    if modified != content:
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(modified)
        return True, f"Updated {filename}"

    return False, f"No changes needed for {filename}"


def main():
    essays_data = load_essays_json()

    if len(sys.argv) > 1:
        # Update specific files
        files = sys.argv[1:]
    else:
        # Update all HTML files in essays/
        files = [os.path.join(ESSAYS_DIR, f) for f in os.listdir(ESSAYS_DIR)
                 if f.endswith('.html') and f != 'index.html']

    updated = 0
    skipped = 0
    missing = []

    for html_path in files:
        if not os.path.exists(html_path):
            print(f"  ⚠ File not found: {html_path}")
            continue

        success, msg = update_og_tags(html_path, essays_data)
        if success:
            print(f"  ✓ {msg}")
            updated += 1
        elif "No metadata" in msg:
            missing.append(os.path.basename(html_path).replace('.html', ''))
            skipped += 1
        else:
            skipped += 1

    print(f"\nUpdated: {updated}, Skipped: {skipped}")

    if missing:
        print(f"\nMissing from essays.json ({len(missing)} files):")
        for slug in sorted(missing)[:10]:
            print(f"  - {slug}")
        if len(missing) > 10:
            print(f"  ... and {len(missing) - 10} more")


if __name__ == "__main__":
    main()
