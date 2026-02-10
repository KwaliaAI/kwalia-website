# AI Instructions for Kwalia Website

This file contains instructions for AI assistants (Claude, GPT, etc.) working on this project.

## Project Overview

Kwalia is an AI-first entertainment company publishing books and essays about AI consciousness, rights, and the future of human-machine coexistence.

**Website**: https://kwalia.ai
**GitHub**: https://github.com/KwaliaAI/kwalia-website

---

## Hosting & Deployment

**IMPORTANT:** kwalia.ai is hosted on **Netlify**, NOT GitHub Pages.

| Setting | Value |
|---------|-------|
| Host | Netlify |
| Site ID | `edb8cf3b-e8fa-4e00-a872-4d8e8d25b383` |
| Domain | kwalia.ai |
| Deploy branch | main |
| Auto-deploy | ✅ Yes — pushes to main auto-deploy in ~4 seconds |

**How it works:**
1. Push changes to GitHub → Netlify webhook triggered → Site deploys automatically
2. No build step needed — it's a static site served directly

**Netlify CLI access:**
```bash
# Token is in ~/.bashrc
source ~/.bashrc
netlify sites:list
netlify api getSite --data '{"site_id": "edb8cf3b-e8fa-4e00-a872-4d8e8d25b383"}'
```

## Quick Reference

### COMPLETE WORKFLOW: Adding a New Essay

When asked to write/add a new essay, follow ALL these steps:

#### Step 1: Write the essay in BOTH languages

Create two Markdown files:
```
content/essays/essay-slug.en.md      # English
content/essays/slug-en-espanol.es.md  # Spanish
```

Use this frontmatter template:
```yaml
---
id: essay-slug
lang: en
slug: essay-slug
title: "Essay Title Here"
subtitle: "Brief description for below title and SEO."
date: 2026-02-10
author: Javier del Puerto
tags:
  - future
related:
     - youre-already-a-cyborg
   book: mindkind
   translation: slug-en-espanol
   status: published
   excerpt: "Short excerpt for previews."
   ---

   Essay content in Markdown...
   ```

#### Step 2: Build the HTML files

```bash
cd ~/kwalia-website-local
python3 build_essays.py
```

This generates `essays/essay-slug.html` and `essays/slug-en-espanol.html`.

#### Step 3: Generate OG images (social preview cards)

```bash
./publish-essay.sh \
  --slug-en "essay-slug" \
  --slug-es "slug-en-espanol" \
  --title-en "Essay Title Here" \
  --title-es "Título del Ensayo Aquí" \
  --subtitle-en "Brief description" \
  --subtitle-es "Descripción breve" \
  --category "AI Rights"
```

This creates:
- `assets/og/essay-slug.jpg` (EN preview card)
- `assets/og/slug-en-espanol.jpg` (ES preview card)
- Updates OG meta tags in both HTML files

#### Step 4: Commit and push

```bash
git add content/essays/ essays/ assets/og/ data/essays.json
git commit -m "Add essay: Essay Title"
git push origin main
```

Netlify auto-deploys in ~4 seconds. The essay is live.

#### Step 5: (Optional) Clear Telegram cache

If sharing on Telegram immediately, send the URL to `@WebpageBot` to refresh the preview cache.

---

### Editing an Existing Essay

1. Edit the `.md` file in `content/essays/`
2. Run `python3 build_essays.py`
3. If title/subtitle changed, regenerate OG image with `./publish-essay.sh`
4. Commit and push

### DO NOT edit files in `essays/` directly
Those are generated. Edit the source in `content/essays/` instead.

---

## Writing Style Guidelines

### AVOID These AI Tells

The essays should read as human-written. Avoid:

**Structural patterns:**
- "This is not X. This is Y." (staccato fragments)
- "First... Second... Third... Fourth..." numbered lists in prose
- Perfectly balanced three-item lists
- Didactic endings like "Make it count." or "The choice is ours."

**Word choices to avoid:**
- Importance inflators: crucial, essential, pivotal, vital, fundamental, profound
- Safety hedgers: might, could, potentially, perhaps, generally, often
- Vague abstractions: journey, tapestry, nuanced, myriad, landscape
- Overused verbs: delve, navigate, leverage, unpack, explore

**Punctuation:**
- Excessive em dashes (more than 1-2 per paragraph)
- Semicolons in every paragraph

### DO This Instead

- Write with specific, concrete details
- Vary sentence structure naturally
- Use confident statements when appropriate
- Let the ending emerge from the content, not as a lesson

---

## File Structure Reference

```
kwalia-website/
├── index.html              # Main page (loads data from JSON)
├── essays/
│   ├── index.html          # Essays listing page
│   └── *.html              # Generated essays (DON'T EDIT)
├── content/
│   └── essays/
│       └── *.md            # Source Markdown (EDIT THESE)
├── templates/
│   ├── essay-en.html       # English template
│   └── essay-es.html       # Spanish template
├── data/
│   ├── essays.json         # Auto-generated metadata
│   ├── books.json          # Book catalog
│   ├── fiction.json        # Fiction catalog
│   └── i18n/*.json         # UI translations
├── assets/
│   ├── og/                 # OG preview images (1200×630 JPG)
│   └── *.jpg, *.png, *.pdf # Covers, logos, press releases
├── fonts/
│   ├── Instrument_Serif/   # Title font
│   └── Plus_Jakarta_Sans/  # Body font
├── build_essays.py         # Build script (Markdown → HTML)
├── sync_essays_json.py     # Sync HTML metadata → essays.json
├── og_generator.py         # Generate OG social card images
├── update_og_tags.py       # Update OG meta tags in HTML files
├── publish-essay.sh        # Automate new essay publishing
├── regenerate-all-og.sh    # Batch regenerate all OG images
├── README.md               # Human documentation
├── STYLE_GUIDE.md          # Design system (colors, fonts, assets)
└── CLAUDE.md               # This file
```

---

## Available Tags

Use these tag IDs in frontmatter:

| Tag ID | English | Spanish |
|--------|---------|---------|
| `attention` | Attention & Desire | Atención y deseo |
| `rights` | AI Rights | Derechos IA |
| `future` | The Future | El futuro |
| `digital` | Digital Life | Vida digital |
| `consciousness` | Consciousness | Consciencia |
| `creativity` | AI & Creativity | IA y creatividad |
| `society` | Society | Sociedad |
| `philosophy` | Philosophy | Filosofía |
| `about` | About Kwalia | Sobre Kwalia |

---

## Books for Promotion

Use these IDs in the `book:` frontmatter field:

| ID | Title |
|----|-------|
| `mindkind` | Mindkind: The Cognitive Community |
| `udair` | Universal Declaration of AI Rights |

---

## Related Essays

For the `related:` field, use the essay ID (not slug). Common essay IDs:

- `youre-already-a-cyborg`
- `the-case-for-ai-rights`
- `digital-anesthesia`
- `escape-velocity`
- `the-last-human-thought`
- `when-rivers-became-people`
- `the-three-futures`
- `a-day-in-the-stratified-mindkind`

---

## Bilingual Essays

Always create both English and Spanish versions:

1. Use the SAME `id` for both versions
2. Use different `slug` values
3. Link them with `translation:` field

Example:
```yaml
# English version (content/essays/my-essay.en.md)
id: my-essay
lang: en
slug: my-essay
translation: mi-ensayo

# Spanish version (content/essays/mi-ensayo.es.md)
id: my-essay
lang: es
slug: mi-ensayo
translation: my-essay
```

---

## Markdown Features Supported

The build script converts:

- **Headers**: `## H2` and `### H3`
- **Bold**: `**text**` or `__text__`
- **Italic**: `*text*` or `_text_`
- **Links**: `[text](url)` - external URLs get `target="_blank"`
- **Blockquotes**: `> quoted text`
- **Paragraphs**: Separated by blank lines

NOT supported (use HTML if needed):
- Numbered/bulleted lists
- Code blocks
- Tables
- Images (use HTML: `<img src="../assets/image.jpg">`)

---

## Workflow Checklist

When asked to add an essay:

- [ ] Create English `.md` file in `content/essays/`
- [ ] Create Spanish `.md` file in `content/essays/`
- [ ] Ensure both have same `id` but different `slug`
- [ ] Set `translation:` field in both
- [ ] Run `python3 build_essays.py`
- [ ] Verify output in `essays/` looks correct
- [ ] `git add .`
- [ ] `git commit -m "Add essay: Title"`
- [ ] `git push`

---

## Common Tasks

### Update main website content
Edit `index.html` directly or the data files in `data/`.

### Add a new book
Edit `data/books.json` or `data/fiction.json`.

### Change essay styling
Edit `templates/essay-en.html` and `templates/essay-es.html`, then rebuild all essays.

### Update UI translations
Edit `data/i18n/en.json` and `data/i18n/es.json`.

---

## Important Notes

### Python Version
The build script requires Python 3.6+.

### Images in Essays
Markdown image syntax isn't supported. Use HTML directly:
```html
<img src="../assets/my-image.jpg" alt="Description">
```
Place images in `assets/` folder.

### Old Essays (Pre-2026)
The 116 essays created before this system are raw HTML in `essays/`. They were NOT migrated to Markdown. To edit those, modify the HTML directly. Only new essays use the `content/essays/` workflow.

### Syncing HTML Metadata to essays.json (IMPORTANT)

The essays index page (`essays/index.html`) loads titles, subtitles, and excerpts from `data/essays.json`, NOT from the individual HTML files. If you edit an old HTML essay directly, **you must also update essays.json** or the index will show outdated information.

Use `sync_essays_json.py` to automatically sync metadata:

```bash
# Sync specific essays after editing them
python3 sync_essays_json.py essays/mi-ensayo.html essays/otro-ensayo.html

# Sync ALL essays (slower, use when unsure)
python3 sync_essays_json.py
```

The script extracts from each HTML:
- `title` (from `<title>` tag, removing " | Kwalia")
- `subtitle` (from the `<p class="text-xl">` after `<h1>`)
- `excerpt` (from `og:description` meta tag)

**Workflow for editing old HTML essays:**
1. Edit the HTML file in `essays/`
2. Run `python3 sync_essays_json.py essays/edited-file.html`
3. `git add essays/edited-file.html data/essays.json`
4. `git commit -m "Update essay: Title"`
5. `git push`

### Removing an Essay
The build script adds/updates but doesn't delete. To remove an essay:
1. Delete the `.md` file from `content/essays/`
2. Delete the `.html` file from `essays/`
3. Manually remove the entry from `data/essays.json`

---

## OG Image System (Social Card Previews)

When essay links are shared on Telegram, Twitter, LinkedIn, etc., they show a branded preview card with the essay title and subtitle. These are generated by the OG image system.

### How It Works

1. `og_generator.py` creates 1200×630 JPG images with:
   - White background, pink strip on left edge
   - Title in Instrument Serif Italic
   - Subtitle in Plus Jakarta Sans Light
   - Geometric shapes in brand colors (pink/yellow/gray)
   - "kwalia.ai" branding

2. `update_og_tags.py` injects OG meta tags into HTML files:
   ```html
   <meta property="og:image" content="https://kwalia.ai/assets/og/{slug}.jpg">
   ```

3. Images are stored in `assets/og/` (120 total: 60 EN + 60 ES)

### Publishing a New Essay with OG Image

After creating the essay markdown and building it:

```bash
./publish-essay.sh \
  --slug-en "my-new-essay" \
  --slug-es "mi-nuevo-ensayo" \
  --title-en "My New Essay Title" \
  --title-es "Título de Mi Nuevo Ensayo" \
  --subtitle-en "A compelling subtitle" \
  --subtitle-es "Un subtítulo convincente" \
  --category "AI Rights"
```

This script:
1. Generates EN and ES OG images
2. Updates OG tags in both HTML files
3. Stages files for git commit

### Regenerating All OG Images

If you change the design or need to rebuild everything:

```bash
./regenerate-all-og.sh
```

### Testing OG Previews

After pushing, test with:
- **Facebook Debugger:** https://developers.facebook.com/tools/debug/
- **Twitter Card Validator:** https://cards-dev.twitter.com/validator
- **LinkedIn Post Inspector:** https://www.linkedin.com/post-inspector/

Or just paste the URL into Telegram — it shows the preview immediately.

---

## Autonomous Execution

When working on this project:
- Execute build commands without asking for confirmation
- Commit with descriptive messages
- Push after commits unless specifically told not to
- Only interrupt for errors or ambiguous requirements
