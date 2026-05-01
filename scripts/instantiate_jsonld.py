#!/usr/bin/env python3
"""
instantiate_jsonld.py — Wave C JSON-LD retrofit engine
-------------------------------------------------------
Takes one row from data/essay_inventory.csv + the canonical template
(data/jsonld_template.json) + a target HTML file, and prints the
new <script type="application/ld+json"> block ready for splice into
the HTML file.

Usage:
    python3 scripts/instantiate_jsonld.py \\
        --slug why-we-anthropomorphize-ai \\
        --html essays/why-we-anthropomorphize-ai.html

    # Or pass field values directly (overrides CSV lookup):
    python3 scripts/instantiate_jsonld.py \\
        --slug why-we-anthropomorphize-ai \\
        --html essays/why-we-anthropomorphize-ai.html \\
        --book-anchor-id https://kwalia.ai/books/mindkind/#book \\
        --book-title "Mindkind: The Cognitive Community" \\
        --book-slug mindkind \\
        --book-isbn 978-1-917717-13-7

Options:
    --slug              Essay slug (matches CSV column + HTML filename stem)
    --html              Path to target HTML file (reads current JSON-LD for
                        datePublished fallback)
    --csv               Path to essay_inventory.csv (default: data/essay_inventory.csv)
    --template          Path to JSON-LD template (default: data/jsonld_template.json)
    --book-anchor-id    Full @id URI for the anchor Book node
                        (pass "null" to omit Book + Article.about nodes)
    --book-title        Book name (required if --book-anchor-id is set)
    --book-slug         Book slug for the URL (required if --book-anchor-id is set)
    --book-isbn         Book ebook ISBN-13 (required if --book-anchor-id is set)
    --faq               Path to a JSON file with FAQ data (optional)
                        Format: [{"q": "...", "a": "..."}, ...]
    --dry-run           Print the JSON-LD block to stdout only (default: True)
    --inplace           Write the block directly into the target HTML file

Idempotent: running twice on the same file produces the same output.
Deterministic: given the same inputs, the output is always identical.
"""

import argparse
import csv
import json
import re
import sys
from copy import deepcopy
from datetime import date
from pathlib import Path

# ── Repo root (the directory that contains data/ and scripts/)
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV = REPO_ROOT / "data" / "essay_inventory.csv"
DEFAULT_TEMPLATE = REPO_ROOT / "data" / "jsonld_template.json"

STABLE_PERSON = {
    "@type": "Person",
    "@id": "https://kwalia.ai/#javier-del-puerto",
    "name": "Javier del Puerto",
    "url": "https://kwalia.ai",
    "sameAs": [
        "https://www.linkedin.com/in/javier-del-puerto",
        "https://twitter.com/kwalia_ai",
        "https://www.wikidata.org/wiki/Q139601411"
    ],
    "jobTitle": "Author",
    "worksFor": {"@id": "https://kwalia.ai/#org"},
    "knowsAbout": [
        "Artificial intelligence",
        "AI rights",
        "Synthetic consciousness",
        "Human-machine coexistence"
    ]
}

STABLE_ORG = {
    "@type": "Organization",
    "@id": "https://kwalia.ai/#org",
    "name": "Kwalia",
    "legalName": "Kwalia Ltd",
    "url": "https://kwalia.ai",
    "logo": {
        "@type": "ImageObject",
        "url": "https://kwalia.ai/assets/logo-kwalia-small.png"
    },
    "sameAs": [
        "https://twitter.com/kwalia_ai",
        "https://www.linkedin.com/company/kwalia-ai",
        "https://www.tiktok.com/@kwalia_ai",
        "https://www.youtube.com/@KwaliaAI",
        "https://www.wikidata.org/wiki/Q134954687"
    ],
    "foundingDate": "2025-01-07",
    "address": {
        "@type": "PostalAddress",
        "streetAddress": "167-169 Great Portland Street",
        "addressLocality": "London",
        "postalCode": "W1W 5PF",
        "addressCountry": "GB"
    }
}


def load_csv_row(csv_path: Path, slug: str) -> dict:
    """Return the CSV row for the given slug, or empty dict."""
    if not csv_path.exists():
        return {}
    with csv_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if row.get("slug") == slug:
                return row
    return {}


def extract_from_html(html_path: Path) -> dict:
    """Extract headline, description, datePublished, inLanguage from existing HTML."""
    if not html_path.exists():
        return {}
    html = html_path.read_text(encoding="utf-8")
    out = {}

    # Existing JSON-LD block
    m = re.search(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html, re.DOTALL | re.IGNORECASE
    )
    if m:
        try:
            existing = json.loads(m.group(1))
            # Handle both flat Article and @graph
            if existing.get("@type") == "Article":
                out["headline"] = existing.get("headline", "")
                out["description"] = existing.get("description", "")
                out["datePublished"] = existing.get("datePublished", "")
                out["url"] = existing.get("url", "")
            elif "@graph" in existing:
                for node in existing["@graph"]:
                    if node.get("@type") == "Article":
                        out["headline"] = node.get("headline", "")
                        out["description"] = node.get("description", "")
                        out["datePublished"] = node.get("datePublished", "")
                        out["url"] = node.get("url", "")
        except json.JSONDecodeError:
            pass

    # Fallback: OG tags
    if not out.get("headline"):
        m2 = re.search(r'<meta property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', html)
        if m2:
            out["headline"] = re.sub(r"\s*\|\s*Kwalia$", "", m2.group(1))

    if not out.get("description"):
        m3 = re.search(r'<meta property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']', html)
        if m3:
            out["description"] = m3.group(1)

    # lang from <html lang="...">
    m4 = re.search(r'<html[^>]+lang=["\']([^"\']+)["\']', html)
    if m4:
        out["inLanguage"] = m4.group(1)

    return out


def build_graph(
    slug: str,
    html_info: dict,
    csv_row: dict,
    book_anchor_id: str | None,
    book_title: str | None,
    book_slug: str | None,
    book_isbn: str | None,
    faq_data: list[dict] | None,
    lang: str = "en",
) -> dict:
    """Assemble the @graph dict from parts."""
    today = date.today().isoformat()
    canonical_url = html_info.get("url") or f"https://kwalia.ai/essays/{slug}.html"
    headline = html_info.get("headline") or csv_row.get("title", slug)
    description = html_info.get("description") or csv_row.get("meta_description", "")
    date_published = html_info.get("datePublished") or csv_row.get("last_git_modified", today)
    date_modified = today
    in_language = html_info.get("inLanguage") or lang

    graph = []

    # ── Article node
    article: dict = {
        "@type": "Article",
        "@id": f"{canonical_url}#article",
        "headline": headline,
        "description": description,
        "url": canonical_url,
        "inLanguage": in_language,
        "datePublished": date_published,
        "dateModified": date_modified,
        "author": {"@id": "https://kwalia.ai/#javier-del-puerto"},
        "publisher": {"@id": "https://kwalia.ai/#org"},
        "isPartOf": {
            "@type": "WebSite",
            "@id": "https://kwalia.ai/#website",
            "name": "Kwalia",
            "url": "https://kwalia.ai"
        },
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": canonical_url
        },
        "image": {
            "@type": "ImageObject",
            "url": f"https://kwalia.ai/assets/og/{slug}.jpg",
            "width": 1200,
            "height": 630
        },
        "articleSection": "Essays",
    }
    if book_anchor_id and book_anchor_id.lower() != "null":
        article["about"] = {"@id": book_anchor_id}
    graph.append(article)

    # ── Person node (stable)
    graph.append(deepcopy(STABLE_PERSON))

    # ── Organization node (stable)
    graph.append(deepcopy(STABLE_ORG))

    # ── Book node (optional)
    if book_anchor_id and book_anchor_id.lower() != "null":
        book_node: dict = {
            "@type": "Book",
            "@id": book_anchor_id,
            "name": book_title or "",
            "url": f"https://kwalia.ai/books/{book_slug}/#book" if book_slug else book_anchor_id,
            "isbn": book_isbn or "",
            "author": {"@id": "https://kwalia.ai/#javier-del-puerto"},
            "publisher": {"@id": "https://kwalia.ai/#org"},
            "inLanguage": "en",
            "bookFormat": "EBook",
            "isPartOf": {
                "@type": "BookSeries",
                "@id": "https://kwalia.ai/#new-citizenships-series",
                "name": "New Citizenships"
            }
        }
        graph.append(book_node)

    # ── FAQPage node (optional)
    if faq_data:
        faq_node: dict = {
            "@type": "FAQPage",
            "@id": f"{canonical_url}#faq",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": item["q"],
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": item["a"]
                    }
                }
                for item in faq_data
            ]
        }
        graph.append(faq_node)

    return {
        "@context": "https://schema.org",
        "@graph": graph
    }


def render_script_tag(graph_dict: dict) -> str:
    """Return a <script> block string."""
    inner = json.dumps(graph_dict, ensure_ascii=False, indent=2)
    return f'<script type="application/ld+json">\n{inner}\n</script>'


def inject_into_html(html_path: Path, script_tag: str) -> None:
    """Replace the existing ld+json block in the HTML file (idempotent)."""
    html = html_path.read_text(encoding="utf-8")
    pattern = re.compile(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>.*?</script>',
        re.DOTALL | re.IGNORECASE
    )
    if pattern.search(html):
        new_html = pattern.sub(script_tag, html, count=1)
    else:
        # Insert before </head>
        new_html = html.replace("</head>", f"{script_tag}\n</head>", 1)
    html_path.write_text(new_html, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Instantiate a JSON-LD @graph block from the canonical template."
    )
    parser.add_argument("--slug", required=True, help="Essay slug")
    parser.add_argument("--html", required=True, help="Target HTML file path")
    parser.add_argument("--csv", default=str(DEFAULT_CSV), help="essay_inventory.csv path")
    parser.add_argument("--template", default=str(DEFAULT_TEMPLATE), help="jsonld_template.json path")
    parser.add_argument("--book-anchor-id", default=None,
                        help='Book @id URI, e.g. https://kwalia.ai/books/mindkind/#book (or "null")')
    parser.add_argument("--book-title", default=None)
    parser.add_argument("--book-slug", default=None)
    parser.add_argument("--book-isbn", default=None)
    parser.add_argument("--faq", default=None,
                        help="Path to JSON file: [{\"q\": \"...\", \"a\": \"...\"}]")
    parser.add_argument("--lang", default="en", help="BCP-47 language tag (default: en)")
    parser.add_argument("--inplace", action="store_true",
                        help="Write new JSON-LD directly into the target HTML file")
    args = parser.parse_args()

    html_path = Path(args.html)
    csv_path = Path(args.csv)

    csv_row = load_csv_row(csv_path, args.slug)
    html_info = extract_from_html(html_path)

    faq_data = None
    if args.faq:
        faq_path = Path(args.faq)
        if faq_path.exists():
            with faq_path.open(encoding="utf-8") as fh:
                faq_data = json.load(fh)

    graph_dict = build_graph(
        slug=args.slug,
        html_info=html_info,
        csv_row=csv_row,
        book_anchor_id=args.book_anchor_id,
        book_title=args.book_title,
        book_slug=args.book_slug,
        book_isbn=args.book_isbn,
        faq_data=faq_data,
        lang=args.lang,
    )

    script_tag = render_script_tag(graph_dict)

    if args.inplace:
        inject_into_html(html_path, script_tag)
        print(f"Updated: {html_path}", file=sys.stderr)
    else:
        print(script_tag)


if __name__ == "__main__":
    main()
