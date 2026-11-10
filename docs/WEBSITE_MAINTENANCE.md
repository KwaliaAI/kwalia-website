# Website maintenance

Technical owner: DD. Iris reviews appearance; Vera reviews new public words;
Theo verifies Sounds facts; Rae owns campaign order and measured audience results.
GM keeps project/launch closure. Founder commissioned this list on 10 November
2026. It is separate from `_agents/shared/runbooks/TITLE_LAUNCH_CHECKLIST.md`,
which is copied into each title's production folder.

Use this list during an authorised maintenance session and after relevant releases.
No new scheduler, monitor, account or standing audit is installed. Verify the
current site contract, clean GitHub main and actual production deploy first.
Record dated evidence and unresolved items here; missing evidence is unknown.

| Task | Owner | Done when | 10 November audit |
|---|---|---|---|
| English/Spanish entry | DD | `/` opens English despite an old Spanish preference; `/es` opens Spanish; explicit `?lang=en/es`, reload, invalid/blocked browser storage and direct title links work | Defect reproduced; URL-based fix in candidate |
| Language switch and navigation | DD / Iris | Desktop/mobile menus, section anchors, language choice, Back/Forward, title modal open/close and sample return work; signup labels match selected language | Candidate browser checks in progress; no test signup sent |
| Availability | DD / Theo for Sounds | Each published/coming-soon label matches dated primary evidence for at least one exact edition/format/marketplace; import, review, retailer listing and complete launch remain separate | China ebook, Darling audio and Mars audio now verified on Storytel Finland; candidate fixes. Neighbours/Everyone still unverified |
| Store and listening links | DD | Match destination title, ISBN/edition, format, language and marketplace; distinguish bot/region blocks from missing products. Check actual UI links, redirects and duplicate destinations; label different formats distinctly | All25existingURLs fetched; Amazon returns generic HTTP 200 pages without verifiable product identity, Kobo HTTP 403.See audit report for exact counted results; no false PASS |
| Retailer coverage | DD | Add only currently evidenced URLs from existing distribution, catalogue first; regenerate public data and reconcile DB/seed. Check that every offered format has its canonical ISBN in the modal | Primary Storytel publisher+18titlepages checked; exact English ISBN matches backfilled across 14 records; two missing legacy formats corrected |
| Public purchase and prices | DD | Read actual buy controls, selected edition and persisted price per commissioned market; no transaction required | Amazon primary product identity/price currently unverified; retain pending, no invented ASIN or purchase |
| Home, dedicated press, press index | DD / Iris / Vera | Approved newest release listed first at publication; EN/ES article, hero, links, dates and current-title availability agree; older bodies untouched | Existing collection release checked; Sounds release draft pending exact Founder approval |
| Campaign rail | Rae / DD / Iris | Current Founder-selected campaign, approved words/image/colour, correct destination and mobile fit | Volume 5 rail retained; newest title does not automatically replace it |
| Responsive presentation | Iris / DD | Relevant1280/390 EN/ES screens opened, fonts/images load, no overflow, obscured controls or broken modal scrolling | 12 baseline screens opened by Iris; candidate review in progress |
| Forms and contact | DD / Vera | Email/placeholder/button/success/error language and actual form endpoint are correct; test delivery only when explicitly authorised | Form not submitted in this audit; visible label checks only. Success/error translation must be checked before a future form change |
| Internal links and assets | DD | Home/menu/sample/press/essay links, cover and social images resolve; missing resource and runtime errors recorded | Existing indexing contract passes; browser checks in progress |
| Search and metadata | DD | Canonical/hreflang, robots/sitemaps, page titles, structured data, search index and social previews follow current source; no stale generated surface | Existing indexing validator passes; no new search-console submission |
| Deployment and source parity | DD | Reviewed commits, required checks, ready production deploy, live source/data/hash/readbacks and catalogue/DB/seed match | Pending this release; retain evidence in audit report |
| Follow-up and closure | Rae / DD / GM | Real publication/send/count evidence after scheduled slots; dated owner for unknown items; approval rows reflect facts; release is complete only under its existing checklist | Newsletter: 23 sent, 22 delivered, 1 hard bounce10 Nov; LinkedIn actual publication unverified; Wednesday–Friday approved schedules retained |

For every change: fix the canonical source, regenerate derived files, run checks
appropriate to the change, get independent technical/word/look reads where
required, deploy authorised corrections, then check production. New public copy
is drafted and reviewed before Founder exact-text approval. Website publication
does not authorise a press mailing or a new social/newsletter message. Existing
unchanged approvals persist.

Keep this one task list and the dated audit report together. Replace inaccurate
status cells after observed readback; do not spawn another checklist. Prune or
replace this file if the website's maintenance ownership or source changes;
undo the addition with its introducing commit.

Open editorial follow-up: NIST currently uses the approved English synopsis on its Spanish interface, an explicit fallback in the existing listing commission. Prepare a Spanish translation through Gus/Vera and exact Founder approval before replacing public copy; do not invent a translation during a status/link repair.
