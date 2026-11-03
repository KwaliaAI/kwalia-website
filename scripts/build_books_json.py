#!/usr/bin/env python3
"""Build the homepage catalogue; Python 3 stdlib only.

Selection: kwalia-books, English primary records, with explicit channel status
live/updated, or partially_live with a per-format KDP status of live. A routing
plan, published lifecycle or enable_for_sale alone is not channel evidence.
Explicit channel evidence takes precedence over stale title-level sale/stage
flags (Volume 2). Fiamma never appears. Missing-channel rows are reported, not
promoted by inference. Spanish editions are represented by the approved overlay,
not duplicate primary cards. Primary rows without verified channels are retained
with siteVisible=false (including Bliss and legacy essay recommendation targets);
the homepage filters that flag before rendering/deep links.

Field mapping:
| Site field | Source |
| id | title_id |
| imprint, volume | series_title (else approved overlay/imprint), series_number/ailgl_volume |
| imprintLine, featured, sampleUrl, sampleLabel | approved site overlay only |
| title.en | title + ': ' + subtitle, except Library titles use title alone |
| title.es, synopsis.es | approved site overlay; absent => existing English fallback |
| authors | authors (split the catalogue collective ' & ') |
| synopsis.en | blurb_300 verbatim |
| formats | isbn_hc/pb/eb/audio, dashed; inactive audio excluded |
| prices | price_hc/pb/eb/audio_gbp, formatted as £x.xx |
| coverImage | assets/<hc else pb else eb else audio ISBN>.jpg; existing art in overlay |
| stores | explicit KDP ASINs (per-format live only), else approved legacy links;
|        | audiobook-only: catalogue platform_links only, otherwise [] |
| status | published when explicit channel test passes, otherwise pending |

--baseline reproduces the pre-migration eight-row snapshot byte for byte. It is
a migration proof only, NOT the normal selection/mapping: the old forthcoming
Apophenia card, English copy and USD prices conflict with those rules. Normal
generation reports excluded rows and never uses snapshot English copy/prices.
The source manifest records the exact clean catalogue commit and content hash.
Run explicitly after catalogue changes; --check detects stale committed output.
"""
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
FORMATS = (("hc", "hardcover"), ("pb", "paperback"), ("eb", "ebook"), ("audio", "audiobook"))


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


def presentation_for(tid, overlay):
    old = next((r for r in overlay["legacy_rows"] if r["id"] == tid), {})
    fields = ("imprint", "imprintLine", "coverImage", "featured", "sampleUrl", "sampleLabel", "stores")
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
    view = presentation_for(tid, overlay)
    library = row.get("series_title") == "AI Law & Governance Library"
    title = row["title"]
    if row.get("subtitle") and not library:
        title += ": " + row["subtitle"]
    formats = [{"type": kind, "isbn": dashed(row[f"isbn_{short}"])}
               for short, kind in FORMATS if row.get(f"isbn_{short}")
               and (short != "audio" or row.get("audiobook_active") is not False)]
    isbn = next((str(row[f"isbn_{short}"]).replace("-", "") for short, _ in FORMATS
                 if row.get(f"isbn_{short}")), "")
    prices = [{"type": kind, "amount": f"£{Decimal(str(row[f'price_{short}_gbp'])):.2f}"}
              for short, kind in FORMATS if row.get(f"price_{short}_gbp") is not None
              and any(f["type"] == kind for f in formats)]
    book = {"id": tid, "imprint": row.get("series_title") or view.get("imprint") or "Kwalia Books"}
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
                 "status": "published" if channels else "pending"})
    audio_only = bool(formats) and all(f["type"] == "audiobook" for f in formats)
    metadata = row.get("draft_metadata") or {}
    asins = metadata.get("kdp_asins") or {}
    states = metadata.get("kdp_format_status") or {}
    if audio_only:
        book["stores"] = row.get("platform_links") or []
    elif asins:
        book["stores"] = [{"name": "Amazon", "url": f"https://www.amazon.com/dp/{asin}", "type": "book"}
                          for kind, asin in asins.items() if states.get(kind) == "live"]
    else:
        # Preserve approved site URLs rather than deriving an unverified retailer ID
        # from an ISBN alone. Volume 1's ISBN-10 link is already in this overlay.
        book["stores"] = view.get("stores", [])
    for key in ("featured", "sampleUrl", "sampleLabel"):
        if key in view:
            book[key] = view[key]
    if not channels:
        book["siteVisible"] = False
    return book


def generate(rows, overlay):
    books, decisions = [], []
    for row in rows:
        tid = row["title_id"]
        channels = live_channels(row)
        reason = None
        if row.get("imprint") != "kwalia-books":
            reason = "other imprint"
        elif row.get("language") not in (None, "eng", "en"):
            reason = "translation edition; approved bilingual overlay is the site surface"
        elif not row.get("blurb_300"):
            reason = "no approved English synopsis"
        if reason:
            decisions.append({"id": tid, "included": False, "reason": reason})
            continue
        book = build_row(row, overlay, channels)
        books.append(book)
        decisions.append({"id": tid, "included": True, "visible": bool(channels), "channels": channels,
                          **({"reason": "no explicit active channel; lifecycle/sale flag alone is insufficient"} if not channels else {})})
    order = {r["id"]: n for n, r in enumerate(overlay["legacy_rows"])}
    books.sort(key=lambda row: order.get(row["id"], len(order)))
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
        output = encode(overlay["legacy_rows"])
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
    print(json.dumps({"catalogue_commit": commit, "baseline": args.baseline,
                      "books": len(json.loads(output)), "sha256": manifest["books_sha256"], "checked": args.check}))


if __name__ == "__main__":
    main()
