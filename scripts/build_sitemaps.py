#!/usr/bin/env python3
"""
build_sitemaps.py — GEO Wave A
Reads data/essay_inventory.csv and emits:
  sitemap-essays.xml   (changefreq monthly)
  sitemap-books.xml    (changefreq monthly, if rows exist)
  sitemap-news.xml     (changefreq weekly, if rows exist)
  sitemap-answers.xml  (changefreq monthly, if rows exist)
  sitemap-index.xml    (master index referencing the above)

All files are written to the repo root (Netlify publish = ".").
Idempotent: running multiple times produces the same output.
"""

import csv
import sys
from datetime import date
from pathlib import Path
from xml.etree import ElementTree as ET

REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = REPO_ROOT / "data" / "essay_inventory.csv"
BASE_URL = "https://kwalia.ai"

# changefreq by section
CHANGEFREQ = {
    "essays": "monthly",
    "books": "monthly",
    "answers": "monthly",
    "news": "weekly",
}

# Build date for lastmod on sitemap-index entries
TODAY = date.today().isoformat()


def load_inventory():
    if not CSV_PATH.exists():
        print(f"ERROR: {CSV_PATH} not found. Run audit_essays.py first.", file=sys.stderr)
        sys.exit(1)
    with open(CSV_PATH, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def build_urlset(rows, changefreq: str) -> ET.Element:
    """Build a <urlset> element from a list of inventory rows."""
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for row in rows:
        url_el = ET.SubElement(urlset, "url")
        ET.SubElement(url_el, "loc").text = row["url"]
        lastmod = row.get("last_git_modified", "").strip()
        if lastmod:
            ET.SubElement(url_el, "lastmod").text = lastmod
        ET.SubElement(url_el, "changefreq").text = changefreq
    return urlset


def pretty_xml(element: ET.Element) -> str:
    """Return indented XML string with declaration."""
    ET.indent(element, space="  ")
    raw = ET.tostring(element, encoding="unicode", xml_declaration=False)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + raw + "\n"


def write_sitemap(path: Path, element: ET.Element):
    path.write_text(pretty_xml(element), encoding="utf-8")
    print(f"  Wrote {path.name}")


def main():
    rows = load_inventory()

    # Group by section
    by_section: dict[str, list] = {}
    for row in rows:
        section = row["section"]
        by_section.setdefault(section, []).append(row)

    # Track which sitemap files are generated (for sitemap-index)
    generated: list[tuple[str, int]] = []  # (filename, entry_count)

    section_order = ["essays", "books", "answers", "news"]
    for section in section_order:
        section_rows = by_section.get(section, [])
        if not section_rows:
            continue
        freq = CHANGEFREQ.get(section, "monthly")
        sitemap_file = REPO_ROOT / f"sitemap-{section}.xml"
        urlset = build_urlset(section_rows, freq)
        write_sitemap(sitemap_file, urlset)
        generated.append((f"sitemap-{section}.xml", len(section_rows)))

    if not generated:
        print("No rows found. Nothing to write.", file=sys.stderr)
        sys.exit(1)

    # Build sitemap-index.xml
    sitemapindex = ET.Element(
        "sitemapindex", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
    )
    for filename, _ in generated:
        sitemap_el = ET.SubElement(sitemapindex, "sitemap")
        ET.SubElement(sitemap_el, "loc").text = f"{BASE_URL}/{filename}"
        ET.SubElement(sitemap_el, "lastmod").text = TODAY

    index_path = REPO_ROOT / "sitemap-index.xml"
    write_sitemap(index_path, sitemapindex)

    print(f"\nSitemap index: {index_path.name} ({len(generated)} sitemaps)")
    for filename, count in generated:
        print(f"  {filename}: {count} entries")

    return 0


if __name__ == "__main__":
    sys.exit(main())
