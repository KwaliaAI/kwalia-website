#!/usr/bin/env python3
"""
Build script for Kwalia essays.

Converts Markdown essays with YAML frontmatter into HTML pages.
Also generates/updates data/essays.json.

Usage:
    python3 build_essays.py              # Build all essays
    python3 build_essays.py --watch      # Watch for changes (requires watchdog)
    python3 build_essays.py essay-name   # Build specific essay

Requirements:
    - Python 3.8+
    - PyYAML (usually pre-installed)
    - Jinja2 (usually pre-installed)

Directory structure:
    content/essays/en/*.md - English source Markdown files
    content/essays/es/*.md - Spanish source Markdown files
    templates/*.html       - Jinja2 templates
    essays/*.html          - Generated output (don't edit directly)
    data/essays.json       - Generated metadata
"""

import os
import re
import json
import yaml
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

# Paths
BASE_DIR = Path(__file__).parent
CONTENT_DIR = BASE_DIR / "content" / "essays"
TEMPLATES_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "essays"
DATA_DIR = BASE_DIR / "data"

# Book metadata for the "Go Deeper" section
BOOKS = {
    "mindkind": {
        "id": "mindkind",
        "title": "Mindkind: The Cognitive Community",
        "image": "9781917717137.jpg",
        "description": "examines how human and machine cognition are merging, and what it means for the future of thought itself."
    },
    "udair": {
        "id": "udair",
        "title": "Universal Declaration of AI Rights",
        "image": "9781917717021.jpg",
        "description": "proposes a framework for AI rights and personhood in an age of synthetic minds."
    }
}

# Tag labels for display
TAG_LABELS = {
    "en": {
        "attention": "Attention & Desire",
        "rights": "AI Rights",
        "future": "The Future",
        "digital": "Digital Life",
        "consciousness": "Consciousness",
        "creativity": "AI & Creativity",
        "society": "Society",
        "philosophy": "Philosophy",
        "about": "About Kwalia"
    },
    "es": {
        "attention": "Atención y deseo",
        "rights": "Derechos IA",
        "future": "El futuro",
        "digital": "Vida digital",
        "consciousness": "Consciencia",
        "creativity": "IA y creatividad",
        "society": "Sociedad",
        "philosophy": "Filosofía",
        "about": "Sobre Kwalia"
    }
}

# Month names for date formatting
MONTHS = {
    "en": ["", "January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December"],
    "es": ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
           "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
}


def simple_markdown_to_html(text):
    """
    Convert Markdown to HTML using regex.
    Handles: paragraphs, headers, links, bold, italic, blockquotes.
    """
    # Normalize line endings
    text = text.replace('\r\n', '\n')

    # Process blockquotes
    lines = text.split('\n')
    in_blockquote = False
    processed_lines = []
    blockquote_content = []

    for line in lines:
        if line.startswith('> '):
            if not in_blockquote:
                in_blockquote = True
            blockquote_content.append(line[2:])
        else:
            if in_blockquote:
                processed_lines.append('<blockquote>' + ' '.join(blockquote_content) + '</blockquote>')
                blockquote_content = []
                in_blockquote = False
            processed_lines.append(line)

    if in_blockquote:
        processed_lines.append('<blockquote>' + ' '.join(blockquote_content) + '</blockquote>')

    text = '\n'.join(processed_lines)

    # Headers (## Header)
    text = re.sub(r'^## (.+)$', r'<h2 class="font-f1 text-3xl">\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^### (.+)$', r'<h3 class="font-f1 text-2xl">\1</h3>', text, flags=re.MULTILINE)

    # Bold (**text** or __text__)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)

    # Italic (*text* or _text_) - be careful not to match ** or __
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', text)
    text = re.sub(r'(?<!_)_(?!_)(.+?)(?<!_)_(?!_)', r'<em>\1</em>', text)

    # Links [text](url) - handle target="_blank" for external links
    def replace_link(match):
        link_text = match.group(1)
        url = match.group(2)
        if url.startswith('http://') or url.startswith('https://'):
            return f'<a href="{url}" target="_blank" rel="noopener noreferrer">{link_text}</a>'
        else:
            return f'<a href="{url}">{link_text}</a>'

    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replace_link, text)

    # Paragraphs - split by double newlines
    paragraphs = re.split(r'\n\n+', text.strip())
    html_parts = []

    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        # Don't wrap if already has block-level HTML
        if p.startswith('<h2') or p.startswith('<h3') or p.startswith('<blockquote'):
            html_parts.append(p)
        else:
            # Replace single newlines with spaces (for wrapped lines in source)
            p = p.replace('\n', ' ')
            html_parts.append(f'<p>{p}</p>')

    return '\n\n'.join(html_parts)


def parse_frontmatter(content):
    """
    Parse YAML frontmatter from Markdown content.
    Returns (metadata dict, markdown content).
    """
    if not content.startswith('---'):
        return {}, content

    # Find the closing ---
    end_match = re.search(r'\n---\n', content[3:])
    if not end_match:
        return {}, content

    yaml_content = content[3:end_match.start() + 3]
    markdown_content = content[end_match.end() + 3 + 1:]

    try:
        metadata = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}")
        return {}, content

    return metadata or {}, markdown_content


def format_date(date_str, lang):
    """Format date string for display."""
    try:
        if isinstance(date_str, datetime):
            dt = date_str
        else:
            dt = datetime.strptime(str(date_str), "%Y-%m-%d")
        month_name = MONTHS[lang][dt.month]
        return f"{month_name} {dt.year}"
    except:
        return str(date_str)


def estimate_read_time(content):
    """Estimate reading time in minutes (avg 200 words/min)."""
    words = len(content.split())
    return max(1, round(words / 200))


def load_all_essays_metadata():
    """Load metadata from all essay Markdown files."""
    essays = {}
    for md_file in CONTENT_DIR.glob("**/*.md"):
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        metadata, _ = parse_frontmatter(content)
        if metadata.get('id'):
            essays[metadata['id']] = {
                'file': md_file.name,
                **metadata
            }
    return essays


def build_essay(md_file, all_essays=None):
    """Build a single essay from Markdown to HTML."""
    print(f"Building: {md_file.name}")

    # Read source file
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse frontmatter and content
    metadata, markdown_content = parse_frontmatter(content)

    if not metadata.get('id'):
        print(f"  Warning: No 'id' in frontmatter, skipping")
        return None

    lang = metadata.get('lang', 'en')

    # Convert Markdown to HTML
    html_content = simple_markdown_to_html(markdown_content)

    # Prepare template data
    slug = metadata.get('slug', metadata['id'])
    data = {
        'id': metadata['id'],
        'slug': slug,
        'title': metadata.get('title', 'Untitled'),
        'subtitle': metadata.get('subtitle', ''),
        'date': metadata.get('date', ''),
        'date_formatted': format_date(metadata.get('date', ''), lang),
        'author': metadata.get('author', 'Javier del Puerto'),
        'tags': metadata.get('tags', []),
        'tag_labels': TAG_LABELS.get(lang, TAG_LABELS['en']),
        'read_time': metadata.get('read_time') or estimate_read_time(markdown_content),
        'content': html_content,
        'translation_slug': metadata.get('translation'),
    }

    # Add related essays
    if metadata.get('related') and all_essays:
        related_list = []
        for rel_id in metadata['related']:
            if rel_id in all_essays:
                rel = all_essays[rel_id]
                # Get the version in the same language if available
                rel_slug = rel.get('slug', rel_id)
                related_list.append({
                    'slug': rel_slug,
                    'title': rel.get('title', rel_id)
                })
        data['related'] = related_list

    # Add book data
    if metadata.get('book') and metadata['book'] in BOOKS:
        data['book'] = BOOKS[metadata['book']]

    # Load and render template
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template_name = f"essay-{lang}.html"
    try:
        template = env.get_template(template_name)
    except Exception as e:
        print(f"  Error loading template {template_name}: {e}")
        return None

    html_output = template.render(**data)

    # Write output file
    output_file = OUTPUT_DIR / f"{slug}.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_output)

    print(f"  -> {output_file.name}")

    # Return metadata for essays.json
    return {
        'id': metadata['id'],
        'slug': {lang: slug},
        'title': {lang: metadata.get('title', 'Untitled')},
        'subtitle': {lang: metadata.get('subtitle', '')},
        'excerpt': {lang: metadata.get('excerpt', metadata.get('subtitle', ''))},
        'date': str(metadata.get('date', '')),
        'author': metadata.get('author', 'Javier del Puerto'),
        'readTime': data['read_time'],
        'tags': metadata.get('tags', []),
        'status': metadata.get('status', 'published'),
        'translation': metadata.get('translation')
    }


def merge_essay_metadata(existing, new_entry):
    """Merge new essay metadata with existing entry (for bilingual essays)."""
    if not existing:
        return new_entry

    # Merge slug, title, subtitle, excerpt by language
    for key in ['slug', 'title', 'subtitle', 'excerpt']:
        if key in new_entry and new_entry[key]:
            if key not in existing:
                existing[key] = {}
            existing[key].update(new_entry[key])

    return existing


def generate_essay_card_html(essay, lang='en'):
    """Generate HTML for an essay card in the index page."""
    import random
    random.seed(essay['id'])  # Consistent random shapes per essay

    # Generate random SVG shapes
    shapes = []
    shape_types = ['circle', 'rect', 'polygon']
    colors = ['#FF70A6', '#474747', '#ffff00']

    for i in range(5):
        shape = random.choice(shape_types)
        color = random.choice(colors)
        opacity = round(random.uniform(0.5, 0.7), 2)

        if shape == 'circle':
            cx, cy = random.randint(20, 80), random.randint(20, 60)
            r = random.randint(10, 20)
            shapes.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" opacity="{opacity}"/>')
        elif shape == 'rect':
            x, y = random.randint(10, 70), random.randint(10, 55)
            w, h = random.randint(12, 24), random.randint(12, 24)
            rot = random.randint(-15, 15)
            shapes.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}" opacity="{opacity}" transform="rotate({rot} {x+w//2} {y+h//2})"/>')
        else:
            px, py = random.randint(15, 75), random.randint(10, 50)
            shapes.append(f'<polygon points="{px},{py} {px+15},{py+25} {px-15},{py+25}" fill="{color}" opacity="{opacity}"/>')

    svg_content = ''.join(shapes)

    # Get bilingual data
    slug_en = essay.get('slug', {}).get('en', essay['id'])
    slug_es = essay.get('slug', {}).get('es', slug_en)
    title_en = essay.get('title', {}).get('en', essay['id'])
    title_es = essay.get('title', {}).get('es', title_en)
    subtitle_en = essay.get('subtitle', {}).get('en', '')
    subtitle_es = essay.get('subtitle', {}).get('es', subtitle_en)

    # Format date
    date_str = essay.get('date', '')
    try:
        dt = datetime.strptime(str(date_str), "%Y-%m-%d")
        date_en = f"{MONTHS['en'][dt.month]} {dt.year}"
        date_es = f"{MONTHS['es'][dt.month]} {dt.year}"
    except:
        date_en = date_es = str(date_str)

    # Tags
    tags = essay.get('tags', [])
    tags_str = ' '.join(tags)
    tag_badges = ''
    for tag in tags:
        tag_en = TAG_LABELS['en'].get(tag, tag)
        tag_es = TAG_LABELS['es'].get(tag, tag)
        tag_badges += f'''
                            <span class="tag-badge" data-filter="{tag}" data-en="{tag_en}" data-es="{tag_es}">{tag_en}</span>'''

    return f'''
                    <a href="{slug_en}.html" class="essay-card flex items-start gap-4 py-6" data-href-en="{slug_en}.html" data-href-es="{slug_es}.html" data-tags="{tags_str}">
                        <svg class="essay-bubble" viewBox="0 0 100 80" xmlns="http://www.w3.org/2000/svg">
            {svg_content}
        </svg>
                        <div class="flex-1">
                            <p class="font-f3 text-xs text-c2/50 mb-2" data-en="{date_en}" data-es="{date_es}">{date_en}</p>
                        <h2 class="font-f1 text-2xl md:text-3xl transition-colors" data-en="{title_en}" data-es="{title_es}">{title_en}</h2>
                        <p class="font-f2 text-c2/70 mt-2" data-en="{subtitle_en}" data-es="{subtitle_es}">{subtitle_en}</p>
                        <div class="essay-tags mt-2">{tag_badges}
                        </div>
                    </div>
                    </a>
'''


def update_essays_index():
    """Update essays/index.html with any missing essay cards."""
    index_file = OUTPUT_DIR / "index.html"
    json_file = DATA_DIR / "essays.json"

    if not index_file.exists() or not json_file.exists():
        return

    # Load essays.json
    with open(json_file, 'r', encoding='utf-8') as f:
        essays = json.load(f)

    # Load index.html
    with open(index_file, 'r', encoding='utf-8') as f:
        index_html = f.read()

    # Find which essays are already in the index
    existing_slugs = set(re.findall(r'data-href-en="([^"]+)\.html"', index_html))

    # Find missing essays (published only)
    missing = []
    for essay in essays:
        if essay.get('status') != 'published':
            continue
        slug_en = essay.get('slug', {}).get('en', essay['id'])
        if slug_en not in existing_slugs:
            missing.append(essay)

    if not missing:
        return

    print(f"\nAdding {len(missing)} new essay(s) to index page...")

    # Generate HTML for missing essays
    new_cards = ''
    for essay in missing:
        new_cards += generate_essay_card_html(essay)
        slug = essay.get('slug', {}).get('en', essay['id'])
        print(f"  + {slug}")

    # Insert after <div id="essays-list" class="space-y-0">
    insert_point = '<div id="essays-list" class="space-y-0">'
    if insert_point in index_html:
        index_html = index_html.replace(
            insert_point,
            insert_point + new_cards
        )

        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(index_html)

        print(f"  Updated {index_file.name}")


def update_essays_json(essays_metadata):
    """Update data/essays.json with essay metadata."""
    json_file = DATA_DIR / "essays.json"

    # Load existing data
    existing_data = []
    if json_file.exists():
        with open(json_file, 'r', encoding='utf-8') as f:
            try:
                existing_data = json.load(f)
            except:
                existing_data = []

    # Create lookup by id
    existing_by_id = {e['id']: e for e in existing_data if 'id' in e}

    # Merge new metadata
    for entry in essays_metadata:
        if entry and entry.get('id'):
            essay_id = entry['id']
            if essay_id in existing_by_id:
                existing_by_id[essay_id] = merge_essay_metadata(existing_by_id[essay_id], entry)
            else:
                existing_by_id[essay_id] = entry

    # Convert back to list, sorted by date (newest first)
    result = list(existing_by_id.values())
    result.sort(key=lambda x: x.get('date', ''), reverse=True)

    # Write output
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\nUpdated {json_file.name} ({len(result)} essays)")


def build_all():
    """Build all essays from content/essays/."""
    if not CONTENT_DIR.exists():
        print(f"Content directory not found: {CONTENT_DIR}")
        print("Create content/essays/ and add Markdown files.")
        return

    md_files = list(CONTENT_DIR.glob("**/*.md"))
    if not md_files:
        print(f"No Markdown files found in {CONTENT_DIR} (searched recursively)")
        return

    print(f"Found {len(md_files)} Markdown files\n")

    # Load all metadata first (for related essays)
    all_essays = load_all_essays_metadata()

    # Build each essay
    essays_metadata = []
    for md_file in sorted(md_files):
        result = build_essay(md_file, all_essays)
        if result:
            essays_metadata.append(result)

    # Update essays.json
    if essays_metadata:
        update_essays_json(essays_metadata)

    # Update essays/index.html with any missing essays
    update_essays_index()

    print(f"\nBuild complete! {len(essays_metadata)} essays generated.")


def build_single(name):
    """Build a single essay by name (without .md extension)."""
    md_file = None
    # Search in root and subdirectories (en/, es/)
    search_paths = [
        CONTENT_DIR / f"{name}.md",
        CONTENT_DIR / "en" / f"{name}.md",
        CONTENT_DIR / "es" / f"{name}.md",
    ]
    for path in search_paths:
        if path.exists():
            md_file = path
            break

    if not md_file:
        print(f"File not found: {name}.md (searched in content/essays/, en/, es/)")
        return

    all_essays = load_all_essays_metadata()
    result = build_essay(md_file, all_essays)

    if result:
        update_essays_json([result])
        print("\nBuild complete!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--help" or arg == "-h":
            print(__doc__)
        elif arg == "--watch":
            print("Watch mode not implemented. Run manually after changes.")
        else:
            build_single(arg)
    else:
        build_all()
