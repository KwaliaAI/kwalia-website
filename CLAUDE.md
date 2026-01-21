# AI Instructions for Kwalia Website

This file contains instructions for AI assistants (Claude, GPT, etc.) working on this project.

## Project Overview

Kwalia is an AI-first entertainment company publishing books and essays about AI consciousness, rights, and the future of human-machine coexistence.

**Website**: https://kwalia.ai
**GitHub**: https://github.com/KwaliaAI/kwalia-website

## Quick Reference

### Adding a New Essay

1. **Create the Markdown file**:
   ```
   content/essays/essay-slug.en.md    # English
   content/essays/slug-en-espanol.es.md  # Spanish
   ```

2. **Use this frontmatter template**:
   ```yaml
   ---
   id: essay-slug
   lang: en
   slug: essay-slug
   title: "Essay Title Here"
   subtitle: "Brief description for below title and SEO."
   date: 2026-01-21
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

3. **Build**:
   ```bash
   python3 build_essays.py
   ```

4. **Commit**:
   ```bash
   git add .
   git commit -m "Add essay: Essay Title"
   git push
   ```

### Editing an Existing Essay

1. Edit the `.md` file in `content/essays/`
2. Run `python3 build_essays.py`
3. Commit and push

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
├── assets/                  # Images, covers, PDFs
├── build_essays.py         # Build script
├── README.md               # Human documentation
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

### Removing an Essay
The build script adds/updates but doesn't delete. To remove an essay:
1. Delete the `.md` file from `content/essays/`
2. Delete the `.html` file from `essays/`
3. Manually remove the entry from `data/essays.json`

---

## Autonomous Execution

When working on this project:
- Execute build commands without asking for confirmation
- Commit with descriptive messages
- Push after commits unless specifically told not to
- Only interrupt for errors or ambiguous requirements
