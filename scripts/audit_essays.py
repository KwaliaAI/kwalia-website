#!/usr/bin/env python3
"""
audit_essays.py — GEO Wave A
Walks /essays/, /books/, /answers/, /news/ (whatever exists) and emits
data/essay_inventory.csv with one row per HTML article file.

Columns:
  section, slug, url, title, meta_description, jsonld_type, byline,
  last_git_modified, word_count, missing_meta_description, missing_jsonld,
  notes

Idempotent: running multiple times produces the same output.
"""

import csv
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parent.parent
BASE_URL = "https://kwalia.ai"
SECTIONS = ["essays", "books", "answers", "news"]
OUT_CSV = REPO_ROOT / "data" / "essay_inventory.csv"

FIELDNAMES = [
    "section",
    "slug",
    "url",
    "title",
    "meta_description",
    "jsonld_type",
    "byline",
    "last_git_modified",
    "word_count",
    "missing_meta_description",
    "missing_jsonld",
    "notes",
]


class EssayParser(HTMLParser):
    """Minimal SAX-style parser; extracts title, meta description,
    JSON-LD @type, and visible text for word count."""

    def __init__(self):
        super().__init__()
        self.title = ""
        self.meta_description = ""
        self.jsonld_type = ""
        self.article_author_types = []
        self._in_title = False
        self._in_script_jsonld = False
        self._jsonld_buf = []
        self._in_body = False
        self._skip_tags = set()
        self._visible_text_parts = []
        self._tag_depth_skip = 0

    # ---- overrides ----

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag == "title":
            self._in_title = True
            return

        if tag == "meta":
            name = attrs_dict.get("name", "").lower()
            prop = attrs_dict.get("property", "").lower()
            if name == "description" or prop == "og:description":
                if not self.meta_description:
                    self.meta_description = attrs_dict.get("content", "")
            return

        if tag == "script":
            stype = attrs_dict.get("type", "")
            if stype == "application/ld+json":
                self._in_script_jsonld = True
                self._jsonld_buf = []
            return

        # Track body for word count (skip script/style/nav/header/footer)
        if tag in ("script", "style", "nav", "header", "footer", "noscript"):
            self._tag_depth_skip += 1
            return

        if tag == "body":
            self._in_body = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
            return

        if tag == "script":
            if self._in_script_jsonld:
                raw = "".join(self._jsonld_buf).strip()
                if raw:
                    try:
                        data = json.loads(raw)
                        self.jsonld_type = jsonld_type(data)
                        self.article_author_types.extend(article_author_types(data))
                    except (json.JSONDecodeError, AttributeError):
                        pass
                self._in_script_jsonld = False
                self._jsonld_buf = []
            else:
                if self._tag_depth_skip > 0:
                    self._tag_depth_skip -= 1
            return

        if tag in ("style", "nav", "header", "footer", "noscript"):
            if self._tag_depth_skip > 0:
                self._tag_depth_skip -= 1

    def handle_data(self, data):
        if self._in_title:
            self.title += data
            return

        if self._in_script_jsonld:
            self._jsonld_buf.append(data)
            return

        if self._in_body and self._tag_depth_skip == 0:
            stripped = data.strip()
            if stripped:
                self._visible_text_parts.append(stripped)

    # ---- helpers ----

    def word_count(self):
        combined = " ".join(self._visible_text_parts)
        return len(combined.split())


def jsonld_type(value) -> str:
    if isinstance(value, dict):
        direct_type = value.get("@type")
        if direct_type:
            return direct_type
        graph = value.get("@graph")
        if isinstance(graph, list):
            for item in graph:
                item_type = jsonld_type(item)
                if item_type == "Article":
                    return item_type
            for item in graph:
                item_type = jsonld_type(item)
                if item_type:
                    return item_type
    elif isinstance(value, list):
        for item in value:
            item_type = jsonld_type(item)
            if item_type:
                return item_type
    return ""


def article_nodes(value):
    if isinstance(value, dict):
        if value.get("@type") == "Article":
            yield value
        graph = value.get("@graph")
        if isinstance(graph, list):
            for item in graph:
                yield from article_nodes(item)
    elif isinstance(value, list):
        for item in value:
            yield from article_nodes(item)


def jsonld_type_values(value) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def jsonld_id_aliases(node_id) -> list[str]:
    if not isinstance(node_id, str) or not node_id:
        return []

    aliases = [node_id]
    parsed = urlsplit(node_id)
    if parsed.fragment:
        aliases.append(f"#{parsed.fragment}")
    if node_id.startswith("#"):
        aliases.append(f"{BASE_URL}/{node_id}")

    deduped = []
    for alias in aliases:
        if alias not in deduped:
            deduped.append(alias)
    return deduped


def jsonld_nodes(value):
    if isinstance(value, dict):
        if "@id" in value and len(value) > 1:
            yield value
        graph = value.get("@graph")
        if isinstance(graph, list):
            for item in graph:
                yield from jsonld_nodes(item)
        for key, item in value.items():
            if key == "@graph":
                continue
            if isinstance(item, (dict, list)):
                yield from jsonld_nodes(item)
    elif isinstance(value, list):
        for item in value:
            yield from jsonld_nodes(item)


def jsonld_node_index(value) -> dict[str, dict]:
    nodes = {}
    for node in jsonld_nodes(value):
        for alias in jsonld_id_aliases(node.get("@id")):
            nodes.setdefault(alias, node)
    return nodes


def resolve_jsonld_reference(value: dict, nodes_by_id: dict[str, dict]) -> dict | None:
    ref_id = value.get("@id")
    if not isinstance(ref_id, str):
        return None
    for alias in jsonld_id_aliases(ref_id):
        node = nodes_by_id.get(alias)
        if node is not None and node is not value:
            return node
    return None


def author_type_values(author, nodes_by_id: dict[str, dict], seen: set[str] | None = None) -> list[str]:
    seen = seen or set()
    if isinstance(author, list):
        values = []
        for item in author:
            values.extend(author_type_values(item, nodes_by_id, seen))
        return values
    if not isinstance(author, dict):
        return []

    types = jsonld_type_values(author.get("@type"))
    if types:
        return types
    if author.get("name") == "Kwalia":
        return ["Organization"]

    ref_id = author.get("@id")
    if isinstance(ref_id, str):
        if ref_id in seen:
            return []
        referenced = resolve_jsonld_reference(author, nodes_by_id)
        if referenced is not None:
            return author_type_values(referenced, nodes_by_id, seen | {ref_id})
    return []


def article_author_types(value) -> list[str]:
    author_types = []
    nodes_by_id = jsonld_node_index(value)
    for article in article_nodes(value):
        authors = article.get("author")
        if isinstance(authors, dict):
            authors = [authors]
        if not isinstance(authors, list):
            continue
        for author in authors:
            author_types.extend(author_type_values(author, nodes_by_id))
    return author_types


def git_last_modified(filepath: Path) -> str:
    """Return ISO-8601 date of last git commit that touched filepath,
    or file mtime as fallback."""
    try:
        relpath = filepath.relative_to(REPO_ROOT).as_posix()
        result = subprocess.run(
            ["git", "log", "--follow", "--format=%ai", "--", relpath],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            timeout=10,
        )
        lines = result.stdout.strip().splitlines()
        if lines:
            raw = lines[0].strip()
            # parse and return YYYY-MM-DD
            dt = datetime.fromisoformat(raw)
            return dt.date().isoformat()
    except Exception:
        pass
    # fallback: file mtime
    mtime = os.path.getmtime(filepath)
    return datetime.fromtimestamp(mtime, tz=timezone.utc).date().isoformat()


def detect_byline(html_text: str) -> str:
    """Look for Javier del Puerto or other named bylines in the HTML body."""
    if "Javier del Puerto" in html_text:
        return "Javier del Puerto"
    # Fallback patterns: author-signature span or itemprop
    m = re.search(
        r'itemprop=["\']author["\'][^>]*>\s*<[^>]+>\s*([^<]{3,60})', html_text
    )
    if m:
        candidate = m.group(1).strip()
        if candidate:
            return candidate
    return ""


def audit_html_file(filepath: Path, section: str):
    """Parse one HTML file and return a dict of fields."""
    html_text = filepath.read_text(encoding="utf-8", errors="replace")

    parser = EssayParser()
    parser.feed(html_text)

    slug = filepath.stem  # filename without .html
    url_slug = slug if section == "essays" else filepath.name
    url = f"{BASE_URL}/{section}/{url_slug}"

    title = parser.title.strip()
    # Strip " | Kwalia" suffix if present
    if title.endswith(" | Kwalia"):
        title = title[: -len(" | Kwalia")].strip()

    meta_desc = parser.meta_description.strip()
    jsonld_type = parser.jsonld_type.strip() if parser.jsonld_type else ""
    byline = detect_byline(html_text)
    last_mod = git_last_modified(filepath)
    wc = parser.word_count()

    notes_parts = []

    # Anomaly detection
    missing_meta = not bool(meta_desc)
    missing_jsonld = not bool(jsonld_type)

    if missing_meta:
        notes_parts.append("MISSING meta_description")
    if missing_jsonld:
        notes_parts.append("MISSING JSON-LD")
    if jsonld_type and jsonld_type not in ("Article", "NewsArticle", "BlogPosting"):
        notes_parts.append(f"JSON-LD @type={jsonld_type} (not Article)")
    if not byline:
        notes_parts.append("NO byline detected")
    if wc < 200:
        notes_parts.append(f"LOW word count ({wc})")

    # Check JSON-LD Article author — should be Person, including @id refs.
    for author_type in sorted({value for value in parser.article_author_types if value != "Person"}):
        notes_parts.append(f"author @type={author_type} (should be Person per GEO mandate)")

    return {
        "section": section,
        "slug": slug,
        "url": url,
        "title": title,
        "meta_description": meta_desc,
        "jsonld_type": jsonld_type,
        "byline": byline,
        "last_git_modified": last_mod,
        "word_count": wc,
        "missing_meta_description": missing_meta,
        "missing_jsonld": missing_jsonld,
        "notes": "; ".join(notes_parts),
    }


def is_article_file(path: Path) -> bool:
    """Exclude index/listing pages; include per-article HTML."""
    return path.suffix == ".html" and path.stem not in ("index",)


def main():
    rows = []
    for section in SECTIONS:
        section_dir = REPO_ROOT / section
        if not section_dir.is_dir():
            continue
        html_files = sorted(f for f in section_dir.iterdir() if is_article_file(f))
        for filepath in html_files:
            row = audit_html_file(filepath, section)
            rows.append(row)

    # Ensure data/ directory exists
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    counts = {}
    for r in rows:
        counts[r["section"]] = counts.get(r["section"], 0) + 1

    print(f"Wrote {len(rows)} rows to {OUT_CSV}")
    for section, count in counts.items():
        print(f"  {section}: {count} files")

    # Surface anomalies
    anomalies = [r for r in rows if r["notes"]]
    if anomalies:
        print(f"\nAnomalies ({len(anomalies)} files):")
        for r in anomalies[:20]:
            print(f"  [{r['section']}] {r['slug']}: {r['notes']}")
        if len(anomalies) > 20:
            print(f"  ... and {len(anomalies) - 20} more. See CSV for full list.")
    else:
        print("\nNo anomalies detected.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
