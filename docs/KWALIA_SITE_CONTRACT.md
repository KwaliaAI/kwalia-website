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
| Homepage book catalogue | `KwaliaAI/catalog` `data/catalog.json` + approved presentation in `data/books.overrides.json` | **GENERATED** `data/books.json`, provenance/selection in `data/books.source.json` | `python3 scripts/build_books_json.py <catalogue-path>`, then repeat with `--check`; `python3 scripts/test_books_builder.py`; indexing validator and desktop/mobile EN/ES smoke |
| Essay article content | `content/essays/en/*.md`, `content/essays/es/*.md` | `essays/*.html`, `data/essays.json` | `python3 build_essays.py`, then indexing contract |
| Historical/manual essay pages | `essays/*.html` only when no Markdown source exists | `data/essays.json` after sync | `python3 sync_essays_json.py`, then indexing contract |
| Essay navigation (index, generated and historical articles) | `templates/essay-nav-links.html`, homepage labels in `data/i18n/*.json` | `build_essays.py` refreshes both menus across `essays/*.html`; language switches retained | Indexing validator checks menu links/order/labels; desktop/mobile live readback |
| Essay listing and search | `data/essays.json`, `build_essays.py`, `essays/index.html` | Search cards embedded in `essays/index.html` | `python3 scripts/validate_indexing_contract.py` |
| Canonical, hreflang, sitemap, internal links | Essay HTML, `data/essays.json`, sitemap XML files | Search engine crawl contract | `python3 scripts/validate_indexing_contract.py` |
| OG/social cards | `assets/og/*.jpg`, `og_generator.py`, `update_og_tags.py`, `publish-essay.sh` | OG image references in essay HTML | Regenerate when title/subtitle changes |
| UI copy and translations | `data/i18n/en.json`, `data/i18n/es.json`, relevant HTML | Rendered language toggle text | Manual browser smoke check |
| Styling and design tokens | `STYLE_GUIDE.md`, inline Tailwind classes, templates | Rendered pages | Desktop/mobile visual check for touched pages |

## Mandatory Workflow

For books, use a clean committed catalogue checkout. The builder defaults to
`../catalog/data/catalog.json`; pass an explicit path when using a worktree.
`books.source.json` records the exact catalogue commit and SHA256, overlay hash,
output hash and row selection decisions. Regenerate after catalogue merges or
approved overlay changes; this is an explicit cross-repository sync, not a runtime
Supabase query or an automatic cross-repository deployment trigger. Never edit
generated book data directly. CI validates artifact hashes and mapping/selection
regressions; the local `--check` verifies against the recorded catalogue input.

The explicit channel test and field mapping are in the builder header. A primary
row is visible when that test passes OR its approved overlay row has
`legacyVisible: true`. The latter is transitional and ends when catalogue channel
evidence is backfilled for those rows. Missing evidence is a catalogue gap, not
proof that an approved legacy title is off sale. Routing plans and lifecycle/sale
flags alone still do not prove channel availability.

All eight approved legacy rows keep their approved text, authors, prices, status, art and sample controls in production order. Under the Founder's10November2026 store-link audit commission, explicit verified catalogue retailer links are merged into those rows and previously omitted offered formats are added with their canonical ISBNs; no prose or planned price is inferred. Approved legacy values win over conflicting catalogue values until the
Founder approves replacement. Channel backfill does not approve copy changes.
Apophenia remains the approved forthcoming card. The overlay visibility control
is stripped from generated public data. `--baseline` reproduces the original eight
public records byte for byte for migration checks; normal generation preserves
their approved fields with the verified link/format exception above and includes
additional commissioned titles according to current channel evidence. PAYLOAD
stays on its existing fiction surface. Current Bliss visibility/store links follow
its observed retailer records and generated selection manifest, not rollout-era
fixed counts or a historical hidden-row example.

For new titles, catalogue English copy/GBP prices and approved presentation fields
are mapped as documented in the builder. Missing Spanish uses the existing English
fallback. New retail links use explicit catalogue ASINs only for live formats;
Volume 2 has one Kindle link, with no print link while print is still publishing.
The Founder commissioned pending Vol 3/4 cards on 2026-11-06. Their catalogue
`draft_metadata.site_listing.visible` permits a forthcoming card without any
storefront-live claim; `site_listing.formats` limits publicly offered formats.
All allocated ISBNs and planned prices stay in the catalogue. Vol 4 exposes only
its accepted Bookwire ebook while KDP creation is blocked. The existing EN copy
fallback on the ES interface is preserved when no approved translation exists.
Store links still require independent live evidence; import acceptance and KDP
review do not activate a channel. Undo this commission by clearing the two
`site_listing.visible` values and regenerating from the committed catalogue.
The source manifest records channels and the legacy exception separately for each
row, without inventing channel status. Retire the legacy visibility exception per
row after verified channel backfill; retain approved field precedence until the
Founder approves any differences.

Undo before merge: close the catalogue and website PRs. Retire the builder if
the homepage catalogue moves to another reviewed source; remove its overlay,
manifest and test step together. Production readback remains GM's post-merge step.

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

## Spanish audit and draft integration (2026-09-24)

- `status: draft` Markdown is excluded from rendering and metadata lookup. A draft replacement never overwrites an existing published HTML page. Change to `published` only after the required editorial approval.
- Reviewed Spanish title/subtitle metadata also refreshes historical HTML chrome via `update_spanish_chrome`; article bodies remain untouched. Spanish Markdown front matter remains authoritative for generated articles.
- `python3 scripts/validate_es_text.py --json /tmp/spanish-findings.json` is a read-only release check requested by the GM audit. It reports question punctuation, banned constructions, em-dashes, title-case candidates and paired body word-count ratios. It cannot certify translation completeness or resolve ambiguous sentence boundaries; findings need human adjudication. No term-wide conciencia/consciencia rewrite is permitted.
- GM’s later 2026-09-24 entry-block dispatch authorizes staged publication: CI gates the sixteen explicitly approved replacement essays and their metadata with `--pages`, while reporting the full remaining backlog separately. The full-site scanner is not green. Expand the gated list as subsequent batches clear GM review. Founder-authored prose is not rewritten to satisfy heuristic flags. Retire/replace the check if Spanish publishing is retired or a better reviewed check supersedes it; undo via the introducing PR's revert.

The second GM batch approval explicitly preserves dialogue rayas in `un-dia-en-el-mindkind-estratificado`. The scanner permits dashes only on dialogue lines there, not narrative parentheticals. Cited English paper titles retain their own question punctuation. The Founder’s untouched essay remains outside the replacement scope.

## Public title copy and metadata — Founder order, 2026-11-03

The catalogue is the single source of truth for all public title copy and metadata, including title, subtitle, author line, description, formats, prices and retailer links. An approved change lands in the catalogue first; the site regenerates from that record and store re-sends carry it through the existing delivery pipelines. No surface is edited directly. The transitional approved legacy overlay preserves current public values until the Founder resolves the parity report; it does not authorize new copy or a direct surface edit. Retire this paragraph only if the Founder replaces the catalogue as the canonical source.

## 10 November2026 website audit

The homepage URL now defines language: `/` English, `/es` Spanish, explicit `?lang=en/es` takes precedence. The toggle updates that URL while preserving tracking parameters and title fragments. A previously saved Spanish value cannot override the English entry route; unavailable storage cannot stop rendering.

Verified existing-channel retailer URLs live in `distribution_plan.<format>.platform_links`, with per-link primary observation evidence and exact ISBN/format/language. Non-legacy live KDP ASIN links retain their format for distinct translated button labels. Explicit wide links are merged alongside Amazon links; one retailer/format is not duplicated merely because a second regional URL was observed. Live retailer observations are scoped to the evidencedmarketplace; they do not certify global availability, prices, checkout or complete launch. Ingestion notes are retained as history.

The separate technical task list is `docs/WEBSITE_MAINTENANCE.md`; the existing company `runbooks/TITLE_LAUNCH_CHECKLIST.md` remains the reusable per-title launch source. No new monitor or automatic wake is installed.
