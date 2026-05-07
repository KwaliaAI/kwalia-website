#!/usr/bin/env python3
"""
Repair the static indexing contract for kwalia.ai.

This is intentionally deterministic because many existing essay HTML files are
historical generated output and are not all rebuildable from current Markdown.
It adds canonical/hreflang tags and normalizes internal hrefs that point to
accented slug variants when the deployed slug is ASCII.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit, urlunsplit

REPO_ROOT = Path(__file__).resolve().parent.parent
BASE_URL = "https://kwalia.ai"
ESSAYS_JSON = REPO_ROOT / "data" / "essays.json"

INDEXING_BLOCK_RE = re.compile(
    r"\n?\s*<!-- Indexing contract -->.*?<!-- /Indexing contract -->\n?",
    re.DOTALL,
)
CANONICAL_LINK_RE = re.compile(
    r"^\s*<link\s+rel=[\"']canonical[\"'][^>]*>\s*\n?",
    re.MULTILINE | re.IGNORECASE,
)
HREFLANG_LINK_RE = re.compile(
    r"^\s*<link\s+rel=[\"']alternate[\"'][^>]*hreflang=[\"'][^\"']+[\"'][^>]*>\s*\n?",
    re.MULTILINE | re.IGNORECASE,
)
HREF_RE = re.compile(r"(?P<prefix>\bhref=)(?P<quote>[\"'])(?P<value>[^\"']*)(?P=quote)")
KWALIA_ESSAY_URL_RE = re.compile(r"https://kwalia\.ai(?P<path>/essays/[^\"'<>\s)]+)")
LEGACY_SLUGS = {
    "three-futures.html": "the-three-futures.html",
    "ya-eres-un-ciborg.html": "ya-eres-un-cyborg.html",
}


def strip_accents(value: str) -> str:
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(char)
    )


def load_slug_pairs() -> tuple[dict[str, dict[str, str]], dict[str, str]]:
    entries = json.loads(ESSAYS_JSON.read_text(encoding="utf-8"))
    pairs_by_slug: dict[str, dict[str, str]] = {}
    lang_by_slug: dict[str, str] = {}

    for entry in entries:
        slug_data = entry.get("slug", {})
        if not isinstance(slug_data, dict):
            continue

        en_slug = slug_data.get("en")
        es_slug = slug_data.get("es")
        pair = {k: v for k, v in {"en": en_slug, "es": es_slug}.items() if v}

        if en_slug:
            pairs_by_slug[en_slug] = pair
            lang_by_slug[en_slug] = "en"
        if es_slug:
            pairs_by_slug[es_slug] = pair
            lang_by_slug[es_slug] = "es"

    return pairs_by_slug, lang_by_slug


def build_indexing_block(canonical_url: str, alternates: list[tuple[str, str]]) -> str:
    lines = [
        "    <!-- Indexing contract -->",
        f'    <link rel="canonical" href="{canonical_url}">',
    ]
    for hreflang, href in alternates:
        lines.append(f'    <link rel="alternate" hreflang="{hreflang}" href="{href}">')
    lines.append("    <!-- /Indexing contract -->")
    return "\n".join(lines) + "\n"


def remove_existing_indexing_tags(html: str) -> str:
    html = INDEXING_BLOCK_RE.sub("\n", html)
    html = CANONICAL_LINK_RE.sub("", html)
    html = HREFLANG_LINK_RE.sub("", html)
    return html


def insert_indexing_block(html: str, canonical_url: str, alternates: list[tuple[str, str]]) -> str:
    block = build_indexing_block(canonical_url, alternates)
    html = remove_existing_indexing_tags(html)

    viewport = re.search(r"^(\s*<meta\s+name=[\"']viewport[\"'][^>]*>\s*\n)", html, re.MULTILINE)
    if viewport:
        return html[: viewport.end()] + block + html[viewport.end() :]

    head = re.search(r"(<head>\s*\n)", html, re.IGNORECASE)
    if head:
        return html[: head.end()] + block + html[head.end() :]

    raise ValueError("HTML file has no <head> insertion point")


def local_page_exists_from_path(path: Path, url_path: str) -> bool:
    decoded_path = unquote(url_path)
    if not decoded_path:
        return False

    if decoded_path.startswith("/"):
        base = REPO_ROOT
        rel = decoded_path.lstrip("/")
    else:
        base = path.parent
        rel = decoded_path

    target = (base / rel).resolve()
    repo = REPO_ROOT.resolve()
    if repo not in target.parents and target != repo:
        return False

    candidates = [target]
    if decoded_path.endswith("/"):
        candidates = [target / "index.html"]
    elif not decoded_path.endswith(".html"):
        candidates.extend([Path(str(target) + ".html"), target / "index.html"])

    return any(candidate.exists() for candidate in candidates)


def normalize_internal_href(path: Path, href: str) -> str:
    if not href or href.startswith(("mailto:", "tel:", "#", "javascript:", "data:")):
        return href

    parsed = urlsplit(href)
    if parsed.scheme and parsed.scheme not in ("http", "https"):
        return href
    if parsed.netloc and parsed.netloc not in ("kwalia.ai", "www.kwalia.ai"):
        return href

    decoded_path = unquote(parsed.path)
    path_parts = decoded_path.rsplit("/", 1)
    filename = path_parts[-1]
    legacy_filename = LEGACY_SLUGS.get(filename)
    if legacy_filename:
        normalized_path = (
            f"{path_parts[0]}/{legacy_filename}" if len(path_parts) == 2 else legacy_filename
        )
    else:
        normalized_path = strip_accents(decoded_path)

    if normalized_path == decoded_path:
        return href
    if not local_page_exists_from_path(path, normalized_path):
        return href

    safe_path = quote(normalized_path, safe="/.:_-~%")
    return urlunsplit((parsed.scheme, parsed.netloc, safe_path, parsed.query, parsed.fragment))


def normalize_internal_hrefs(path: Path, html: str) -> tuple[str, int]:
    changed = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal changed
        href = match.group("value")
        normalized = normalize_internal_href(path, href)
        if normalized != href:
            changed += 1
        return f"{match.group('prefix')}{match.group('quote')}{normalized}{match.group('quote')}"

    return HREF_RE.sub(replace, html), changed


def normalize_embedded_kwalia_urls(path: Path, html: str) -> tuple[str, int]:
    changed = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal changed
        url_path = unquote(match.group("path"))
        normalized_path = strip_accents(url_path)
        if normalized_path == url_path:
            return match.group(0)
        if not local_page_exists_from_path(path, normalized_path):
            return match.group(0)
        changed += 1
        return f"https://kwalia.ai{quote(normalized_path, safe='/:._-~%')}"

    return KWALIA_ESSAY_URL_RE.sub(replace, html), changed


def alternates_for_slug(slug: str, pairs_by_slug: dict[str, dict[str, str]]) -> list[tuple[str, str]]:
    pair = pairs_by_slug.get(slug, {})
    en_slug = pair.get("en")
    es_slug = pair.get("es")
    if not en_slug or not es_slug:
        return []

    return [
        ("en", f"{BASE_URL}/essays/{en_slug}.html"),
        ("es", f"{BASE_URL}/essays/{es_slug}.html"),
        ("x-default", f"{BASE_URL}/essays/{en_slug}.html"),
    ]


def repair_file(path: Path, canonical_url: str, alternates: list[tuple[str, str]]) -> tuple[bool, int]:
    original = path.read_text(encoding="utf-8")
    repaired = insert_indexing_block(original, canonical_url, alternates)
    repaired, href_changes = normalize_internal_hrefs(path, repaired)
    repaired, embedded_url_changes = normalize_embedded_kwalia_urls(path, repaired)
    href_changes += embedded_url_changes
    if repaired != original:
        path.write_text(repaired, encoding="utf-8")
        return True, href_changes
    return False, href_changes


def main() -> int:
    pairs_by_slug, _ = load_slug_pairs()
    changed_files = 0
    changed_hrefs = 0

    fixed, hrefs = repair_file(REPO_ROOT / "index.html", f"{BASE_URL}/", [])
    changed_files += int(fixed)
    changed_hrefs += hrefs

    fixed, hrefs = repair_file(REPO_ROOT / "essays" / "index.html", f"{BASE_URL}/essays/", [])
    changed_files += int(fixed)
    changed_hrefs += hrefs

    for path in sorted((REPO_ROOT / "essays").glob("*.html")):
        if path.name == "index.html":
            continue
        slug = path.stem
        canonical_url = f"{BASE_URL}/essays/{slug}.html"
        alternates = alternates_for_slug(slug, pairs_by_slug)
        fixed, hrefs = repair_file(path, canonical_url, alternates)
        changed_files += int(fixed)
        changed_hrefs += hrefs

    print(f"Repaired indexing contract in {changed_files} file(s).")
    print(f"Normalized {changed_hrefs} internal href(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
