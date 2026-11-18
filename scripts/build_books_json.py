#!/usr/bin/env python3
"""Build the homepage catalogue; Python 3 stdlib only.

Selection: kwalia-books English primary records are visible with explicit channel
status live/updated, or partially_live with a per-format KDP status of live, OR
approved overlay legacyVisible=true. The legacy visibility exception is
transitional: retire it when catalogue channel evidence is backfilled for those
rows. Missing evidence never proves an approved legacy title is off sale.
Routing plans, lifecycle and sale flags alone are not channel evidence. Fiamma
and translation duplicates never appear. Other missing-channel rows are retained
with siteVisible=false for essay readers; verified storefronts use distribution_plan.<format>.platform_links.
An explicit draft_metadata.site_listing.visible commission can display a forthcoming
card without activating a channel. Its formats list limits offered formats while
the catalogue retains all allocated ISBNs. No retailer link is inferred.

Field precedence: an approved legacy row supplies ALL public fields,
including English/Spanish copy, status and prices, verbatim. Founder10Nov2026
authorises merging verified catalogue retailer links and adding previously omitted
offered format ISBNs while retaining existing approved copy.
Catalogue differences require Founder approval before replacement; channel
backfill alone does not approve new public copy. Apophenia stays forthcoming.
The overlay's legacyVisible control is never emitted as a public book field.
For new rows: title/subtitle, authors, blurb_300, series/volume, ISBN formats and
GBP prices come from the catalogue. Art, Spanish copy and sample controls come
from presentation; absent Spanish uses the existing English fallback. Stores use
explicit per-format live KDP ASINs, else approved URLs; audio uses distribution_plan.audiobook.platform_links.

--baseline reproduces the approved eight public rows byte for byte, stripping
only the overlay visibility control. Normal generation preserves these same
rows with their approved copy. Published titles sort by catalogue publication date;
the latest nonfiction title supplies the existing bilingual announcement pattern.
The source manifest records the exact clean catalogue commit and content hash.
Run explicitly after catalogue changes; --check detects stale committed output.
"""
import argparse
from decimal import Decimal
from html import escape
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
FORMATS = (("hc", "hardcover"), ("pb", "paperback"), ("eb", "ebook"), ("audio", "audiobook"))


def release_fields(row):
    fields = {}
    if row.get("date_published"):
        fields["datePublished"] = row["date_published"]
    number = row.get("series_number") or (row.get("draft_metadata") or {}).get("cover_collection_number")
    if number is not None:
        fields["seriesNumber"] = number
    return fields


def latest_announcement(books):
    """Reuse the established title · Volume N of SERIES pattern in EN/ES."""
    latest = next((b for b in books if b["status"] == "published" and b.get("datePublished")
                   and b.get("siteVisible") is not False
                   and b["imprint"] not in ("Kwalia Bliss", "Fiction")), None)
    if latest is None:
        return None
    text = {lang: latest["title"].get(lang) or latest["title"]["en"] for lang in ("en", "es")}
    number = latest.get("seriesNumber") or latest.get("volume")
    if number is not None:
        for lang, pattern in (("en", "Volume {} of {}"), ("es", "Volumen {} de {}")):
            text[lang] += " · " + pattern.format(number, latest["imprint"])
    return latest, text


def announcement_html(html, books):
    latest = latest_announcement(books)
    if latest is None:
        return html
    book, text = latest
    pattern = r'(<a\s+id="latest-release"\s+href=")[^"]*("[^>]*>)[\s\S]*?(</a>)'
    html, count = re.subn(pattern, lambda m: m[1] + "#" + book["id"] + m[2]
                         + "\n            " + escape(text["en"]) + "\n        " + m[3], html)
    if count != 1:
        raise ValueError("Expected exactly one generated latest-release announcement")
    return html


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()


def live_channels(row):
    channels = []
    for name, entry in (row.get("channel_delivery_status") or {}).items():
        status = entry.get("status")
        if status in ("live", "updated"):
            channels.append(name)
        elif status == "partially_live" and name == "amazon-kdp":
            states = (row.get("draft_metadata") or {}).get("kdp_format_status", {})
            if any(value == "live" for value in states.values()):
                channels.append(name)
    return channels


def dashed(isbn):
    digits = str(isbn).replace("-", "")
    if len(digits) != 13 or not digits.isdigit() or not digits.startswith("9781917717"):
        raise ValueError(f"ISBN outside the verified Kwalia prefix: {isbn}")
    return f"{digits[:3]}-{digits[3]}-{digits[4:10]}-{digits[10:12]}-{digits[12]}"


def legacy_public(row):
    return {key: value for key, value in row.items() if key != "legacyVisible"}


def retailer_links(row):
    """Explicit format-specific retailer observations, never delivery plans."""
    links = []
    for kind in ("ebook", "paperback", "hardcover", "audiobook"):
        for link in ((row.get("distribution_plan") or {}).get(kind) or {}).get("platform_links") or []:
            links.append({**link, "format": kind})
    return links


def merge_stores(existing, observed):
    links = [dict(link) for link in existing]
    for link in observed:
        # A retailer already present for this format remains one button, even
        # when the observation uses another regional URL for the same edition.
        if any(old["name"] == link["name"] and old["type"] == link["type"]
               and (not old.get("format") or old["format"] == link.get("format")) for old in links):
            continue
        links.append(link)
    return links


def store_priority(link):
    """GM18Nov2026: major shops first; stable ties retain Amazon format order."""
    name = link["name"].casefold().strip()
    priority = {"amazon": 0, "apple books": 1, "google play": 2,
                "google play books": 2, "kobo": 3}
    # The same commission explicitly retains Heise at the end.
    return (priority.get(name, 5 if name == "heise" else 4),
            "" if name in priority else name)


def single_amazon(links, row):
    """Founder18Nov: Amazon always links one verified hardback, or is absent."""
    # Explicit verified catalogue replacements win over stale legacy/deferred
    # presentation links. An allocated ISBN alone never creates a product URL.
    amazon = [s for s in retailer_links(row) if s["name"].casefold() == "amazon"]
    amazon += [s for s in links if s["name"].casefold() == "amazon"]
    asins = (row.get("draft_metadata") or {}).get("kdp_asins") or {}
    def matches(link, kind):
        if link.get("format") == kind:
            return True
        identifier = link["url"].split("/dp/")[-1].split("/")[0].split("?")[0]
        return bool(asins.get(kind)) and identifier == asins[kind]
    selected = next((s for s in amazon if matches(s, "hardcover")), None)
    if selected is not None:
        selected = {**selected, "format": "hardcover"}
    return [s for s in links if s["name"].casefold() != "amazon"] + ([selected] if selected else [])


def fiction_stores(books, rows):
    """Apply the same shop rule to the separate fiction surface; retain its copy."""
    source_rows = {row["title_id"]: row for row in rows}
    return [{**book, "stores": sorted(single_amazon(book.get("stores", []), source_rows[book["id"]]), key=store_priority)}
            for book in books]


def presentation_for(tid, overlay):
    old = next((r for r in overlay["legacy_rows"] if r["id"] == tid), {})
    fields = ("imprint", "imprintLine", "coverImage", "featured", "sampleUrl", "sampleLabel", "stories", "stores")
    result = {key: old[key] for key in fields if key in old}
    for key in ("title", "synopsis"):
        if "es" in old.get(key, {}):
            result[key] = {"es": old[key]["es"]}
    for key, value in overlay.get("presentation", {}).get(tid, {}).items():
        if key not in (*fields, "title", "synopsis"):
            raise ValueError(f"Unsupported presentation override: {tid}.{key}")
        if key in ("title", "synopsis") and set(value) - {"es"}:
            raise ValueError(f"English catalogue copy cannot be overridden: {tid}.{key}")
        result[key] = value
    return result


def build_row(row, overlay, channels):
    tid = row["title_id"]
    old = next((r for r in overlay["legacy_rows"] if r["id"] == tid), {})
    if old:
        book = legacy_public(old)
        book.update(release_fields(row))
        observed = retailer_links(row)
        book["stores"] = merge_stores(book.get("stores", []), observed)
        # New verified editions must also appear in the modal's ISBN list.
        # Preserve all existing legacy copy, prices and format observations.
        book["formats"] = [dict(item) for item in book.get("formats", [])]
        for short, kind in FORMATS:
            if any(link["format"] == kind for link in observed) and row.get(f"isbn_{short}") and not any(item["type"] == kind for item in book["formats"]):
                book["formats"].append({"type": kind, "isbn": dashed(row[f"isbn_{short}"])})
        if not channels and old.get("legacyVisible") is not True:
            book["siteVisible"] = False
        return book
    view = presentation_for(tid, overlay)
    library = row.get("series_title") == "AI Law & Governance Library"
    title = row["title"]
    if row.get("subtitle") and not library:
        title += ": " + row["subtitle"]
    # An explicitly commissioned pending listing is independent of store activation.
    # Keep allocated but unavailable formats (e.g. blocked KDP print) in the
    # catalogue without offering them on the public card.
    listing = (row.get("draft_metadata") or {}).get("site_listing") or {}
    listed_formats = listing.get("formats")
    if listed_formats is not None and channels:
        # A pre-release format restriction must not hide a subsequently confirmed
        # live edition. An allocation or submission alone still adds nothing.
        states = (row.get("draft_metadata") or {}).get("kdp_format_status") or {}
        listed_formats = set(listed_formats) | {kind for kind, state in states.items() if state == "live"}
    formats = [{"type": kind, "isbn": dashed(row[f"isbn_{short}"])}
               for short, kind in FORMATS if row.get(f"isbn_{short}")
               and (listed_formats is None or kind in listed_formats)
               and (short != "audio" or row.get("audiobook_active") is not False)]
    isbn = next((str(row[f"isbn_{short}"]).replace("-", "") for short, _ in FORMATS
                 if row.get(f"isbn_{short}")), "")
    prices = [{"type": kind, "amount": f"£{Decimal(str(row[f'price_{short}_gbp'])):.2f}"}
              for short, kind in FORMATS if row.get(f"price_{short}_gbp") is not None
              and any(f["type"] == kind for f in formats)]
    book = {"id": tid, "imprint": row.get("series_title") or view.get("imprint") or "Kwalia Books",
            **release_fields(row)}
    volume = row.get("series_number") or row.get("ailgl_volume")
    if library and volume is not None:
        book["volume"] = volume
    if view.get("imprintLine"):
        book["imprintLine"] = view["imprintLine"]
    book.update({"title": {"en": title, **view.get("title", {})},
                 "authors": (row.get("authors") or "").split(" & ") if row.get("authors") else [],
                 "coverImage": view.get("coverImage") or {"en": f"assets/{isbn}.jpg"},
                 "synopsis": {"en": row.get("blurb_300") or "", **view.get("synopsis", {})},
                 "formats": formats, "prices": prices,
                 "status": "published" if channels else "forthcoming" if listing.get("visible") is True else "pending"})
    audio_only = bool(formats) and all(f["type"] == "audiobook" for f in formats)
    metadata = row.get("draft_metadata") or {}
    asins = metadata.get("kdp_asins") or {}
    states = metadata.get("kdp_format_status") or {}
    if audio_only:
        book["stores"] = ((row.get("distribution_plan") or {}).get("audiobook") or {}).get("platform_links") or []
    elif asins and not listing.get("verified_storefronts_only"):
        book["stores"] = [{"name": "Amazon", "url": f"https://www.amazon.com/dp/{asin}", "type": "book", "format": kind}
                          for kind, asin in asins.items() if states.get(kind) == "live"]
    else:
        # Preserve approved site URLs rather than deriving an unverified retailer ID
        # from an ISBN alone. Volume 1's ISBN-10 link is already in this overlay.
        book["stores"] = view.get("stores", [])
    book["stores"] = merge_stores(book["stores"], retailer_links(row))
    for key in ("featured", "sampleUrl", "sampleLabel", "stories"):
        if key in view:
            book[key] = view[key]
    if not channels and listing.get("visible") is not True:
        book["siteVisible"] = False
    # Founder-approved site-only Bliss copy (12 Nov) and availability (17 Nov).
    # Retail metadata stays intact; store URLs are verified public observations.
    site_copy = overlay.get("bliss_site_copy", {}).get(tid)
    if site_copy is not None:
        if book["imprint"] != "Kwalia Bliss" or set(site_copy) - {"title", "tag", "synopsis", "status", "stores"}:
            raise ValueError(f"Invalid Bliss site copy: {tid}")
        book.update(site_copy)
    return book


def generate(rows, overlay):
    books, decisions = [], []
    for row in rows:
        tid = row["title_id"]
        channels = live_channels(row)
        legacy = next((r for r in overlay["legacy_rows"] if r["id"] == tid), {})
        legacy_visible = legacy.get("legacyVisible") is True
        reason = None
        if row.get("imprint") != "kwalia-books":
            reason = "other imprint"
        elif row.get("language") not in (None, "eng", "en"):
            reason = "translation edition; approved bilingual overlay is the site surface"
        elif not row.get("blurb_300") and not legacy_visible:
            reason = "no approved English synopsis"
        if reason:
            decisions.append({"id": tid, "included": False, "reason": reason})
            continue
        book = build_row(row, overlay, channels)
        books.append(book)
        pending_listing = (row.get("draft_metadata") or {}).get("site_listing") or {}
        pending_visible = pending_listing.get("visible") is True
        decisions.append({"id": tid, "included": True, "visible": bool(channels) or legacy_visible or pending_visible, "channels": channels,
                          "legacyVisible": legacy_visible,
                          **({"reason": "approved legacy visibility; transitional until catalogue channel backfill"} if legacy_visible and not channels else
                             {"reason": "commissioned pending listing; no storefront-live claim", "listing_authority": pending_listing.get("authority")} if pending_visible and not channels else
                             {"reason": "no explicit active channel; lifecycle/sale flag alone is insufficient"} if not channels else {})})
    # A bounded commission can leave an unrelated existing site state untouched.
    # These explicit holds are removed only when that title is commissioned.
    for book in books:
        hold = overlay.get("deferred_updates", {}).get(book["id"])
        if hold:
            if set(hold["fields"]) - {"status", "siteVisible", "stores"}:
                raise ValueError("Unsupported deferred site field")
            book.update(hold["fields"])
            decision = next(d for d in decisions if d["id"] == book["id"])
            decision.update(visible=book.get("siteVisible") is not False,
                            deferred_update_authority=hold["authority"])
    # Apply after all presentation/deferred overrides so every generated title
    # follows the same rule, including legacy and audiobook-only records.
    source_rows = {row["title_id"]: row for row in rows}
    for book in books:
        links = single_amazon(book.get("stores", []), source_rows[book["id"]])
        book["stores"] = sorted(links, key=store_priority)
    order = {r["id"]: n for n, r in enumerate(overlay["legacy_rows"])}
    books.sort(key=lambda row: order.get(row["id"], len(order)))
    # Stable date ordering replaces both append-only generation and the browser's
    # manual ID list. Undated titles retain their previous relative order.
    books.sort(key=lambda row: row.get("datePublished", "")
               if row["status"] == "published" and row["imprint"] not in ("Kwalia Bliss", "Fiction")
               else "", reverse=True)
    latest = latest_announcement(books)
    if latest:
        latest[0]["announcement"] = latest[1]
    return books, decisions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalogue", nargs="?", type=Path, default=ROOT.parent / "catalog/data/catalog.json")
    parser.add_argument("--output", type=Path, default=ROOT / "data/books.json")
    parser.add_argument("--overrides", type=Path, default=ROOT / "data/books.overrides.json")
    parser.add_argument("--baseline", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    catalogue = args.catalogue.resolve()
    repo = subprocess.check_output(["git", "-C", str(catalogue.parent), "rev-parse", "--show-toplevel"], text=True).strip()
    commit = subprocess.check_output(["git", "-C", repo, "rev-parse", "HEAD"], text=True).strip()
    relative = str(catalogue.relative_to(repo))
    source = catalogue.read_bytes()
    committed = subprocess.check_output(["git", "-C", repo, "show", f"{commit}:{relative}"])
    if source != committed:
        parser.error("Catalogue differs from recorded commit; commit it before generating.")
    rows = json.loads(source)
    overlay = json.loads(args.overrides.read_bytes())
    if args.baseline:
        output = encode([legacy_public(row) for row in overlay["legacy_rows"]])
        if hashlib.sha256(output).hexdigest() != overlay["baseline_sha256"]:
            parser.error("Baseline no longer matches the original eight-row snapshot.")
        decisions = []
    else:
        books, decisions = generate(rows, overlay)
        output = encode(books)
    manifest = {"catalogue_repository": "https://github.com/KwaliaAI/catalog", "catalogue_commit": commit,
                "catalogue_file": relative, "catalogue_sha256": hashlib.sha256(source).hexdigest(),
                "overlay_sha256": hashlib.sha256(args.overrides.read_bytes()).hexdigest(),
                "books_sha256": hashlib.sha256(output).hexdigest(), "decisions": decisions}
    if args.check:
        if args.output.read_bytes() != output or args.output.with_suffix(".source.json").read_bytes() != encode(manifest):
            parser.error("Generated catalogue is stale; rerun the builder.")
    else:
        args.output.write_bytes(output)
        if not args.baseline:
            args.output.with_suffix(".source.json").write_bytes(encode(manifest))
    if not args.baseline:
        fiction = ROOT / "data/fiction.json"
        before_fiction = fiction.read_bytes()
        after_fiction = encode(fiction_stores(json.loads(before_fiction), rows))
        if args.check and before_fiction != after_fiction:
            parser.error("Fiction store links are stale; rerun the builder.")
        if not args.check:
            fiction.write_bytes(after_fiction)
        index = ROOT / "index.html"
        before = index.read_text()
        after = announcement_html(before, books)
        if args.check and before != after:
            parser.error("Generated latest-release announcement is stale; rerun the builder.")
        if not args.check:
            index.write_text(after)
    print(json.dumps({"catalogue_commit": commit, "baseline": args.baseline,
                      "books": len(json.loads(output)), "sha256": manifest["books_sha256"], "checked": args.check}))


if __name__ == "__main__":
    main()
