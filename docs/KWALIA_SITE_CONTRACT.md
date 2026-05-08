# Kwalia Site Contract

This is the canonical technical contract for `kwalia.ai`. Use it before making any site, essay, SEO, indexing, or metadata change.

The contract is a release blocker. If a change touches a generated surface, search/indexing metadata, or deploy behavior, the source, generated artifact, validation gate, and live readback must all agree before the work is considered done.

## Active Source Of Truth

- Active local repo: `/home/oss/workspace/kwalia-website-google-play`
- GitHub repo: `https://github.com/KwaliaAI/kwalia-website`
- Branch deployed by Netlify: `main`
- Production domain: `https://kwalia.ai`
- Netlify site ID: `edb8cf3b-e8fa-4e00-a872-4d8e8d25b383`

Do not use older local clones as canonical without proving they match GitHub `main` and production.

## Source Map

| Surface | Canonical source | Generated or derived files | Required checks |
|---|---|---|---|
| Main homepage | `index.html`, `data/books.json`, `data/fiction.json`, `data/essays.json`, `data/i18n/*.json` | Browser-rendered homepage sections | Static smoke check plus live readback after deploy |
| Essay article content | `content/essays/en/*.md`, `content/essays/es/*.md` | `essays/*.html`, `data/essays.json` | `python3 build_essays.py`, then indexing contract |
| Historical/manual essay pages | `essays/*.html` only when no Markdown source exists | `data/essays.json` after sync | `python3 sync_essays_json.py`, then indexing contract |
| Essay listing and search | `data/essays.json`, `build_essays.py`, `essays/index.html` | Search cards embedded in `essays/index.html` | `python3 scripts/validate_indexing_contract.py` |
| Canonical, hreflang, sitemap, internal links | Essay HTML, `data/essays.json`, sitemap XML files | Search engine crawl contract | `python3 scripts/validate_indexing_contract.py` |
| OG/social cards | `assets/og/*.jpg`, `og_generator.py`, `update_og_tags.py`, `publish-essay.sh` | OG image references in essay HTML | Regenerate when title/subtitle changes |
| UI copy and translations | `data/i18n/en.json`, `data/i18n/es.json`, relevant HTML | Rendered language toggle text | Manual browser smoke check |
| Styling and design tokens | `STYLE_GUIDE.md`, inline Tailwind classes, templates | Rendered pages | Desktop/mobile visual check for touched pages |

## Mandatory Workflow

1. Verify the active repo, branch, and live target before changing anything.
2. Identify which row in the source map the change touches.
3. Edit the canonical source, not the generated file, unless the source map says the file is manual.
4. Run the generator or sync step for every derived surface.
5. Run `python3 scripts/validate_indexing_contract.py`.
6. Push only after the validation gate is green.
7. After Netlify deploys, read production back from `https://kwalia.ai` and prove the changed surface is live.
8. Log the change, including the verification command and live evidence.

## Essay Change Types

### Add A New Essay

- Add both language Markdown files under `content/essays/en/` and `content/essays/es/` when possible.
- Use one shared `id`, language-specific `slug`, complete `title`, `subtitle`, `excerpt`, `tags`, `date`, `author`, `status`, and translation link.
- Run `python3 build_essays.py`.
- Regenerate OG cards with `./publish-essay.sh` if needed.
- Run `python3 scripts/validate_indexing_contract.py`.

### Edit Essay Title, Subtitle, Tags, Slugs, Or Search Text

- Edit Markdown frontmatter when Markdown source exists.
- For historical HTML-only essays, edit the HTML and then run `python3 sync_essays_json.py`.
- Run `python3 build_essays.py` so `essays/index.html` is refreshed from `data/essays.json`.
- Run `python3 scripts/validate_indexing_contract.py`.
- Search locally for the changed title and its expected queries before deploy.

### Edit Essay Body Only

- Edit Markdown source when it exists.
- Run `python3 build_essays.py`.
- Run the indexing contract if the change touches links, headings, slugs, metadata, or related links.

## CI Gate

GitHub Actions runs `.github/workflows/indexing-contract.yml` on pull requests and pushes to `main`.

The gate validates:

- Canonical URL tags.
- Hreflang pairs.
- Sitemap URLs.
- Internal page links.
- Non-ASCII URL and href drift.
- Every published `data/essays.json` entry has a matching card in `essays/index.html`.
- Essay listing card title, subtitle, language hrefs, and tags match `data/essays.json`.
- Essay search indexes title, subtitle/excerpt, tags, and hrefs, with location-independent matching.

Any future incident that exposes a missing technical contract must add a validator before the next similar delivery. Documentation alone is not sufficient.

## 2026-05-08 Lesson

The homepage showed updated essays because it loaded `data/essays.json`, but `/essays/` search used stale card text embedded in `essays/index.html`. The original generator appended missing cards and did not refresh existing ones, so title and metadata edits were left hanging.

The repair was:

- `build_essays.py` now refreshes published listing cards from `data/essays.json`.
- Essay search indexes visible text, English/Spanish title, English/Spanish subtitle, tags, and hrefs.
- The indexing contract now fails if `data/essays.json` and `essays/index.html` drift.

The general rule is: every source-of-truth relationship must have a machine check. If the site can drift silently, the contract is incomplete.
