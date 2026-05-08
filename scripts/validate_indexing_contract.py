#!/usr/bin/env python3
"""
Validate kwalia.ai's static indexing contract.

The gate is intentionally local and free-tier compatible: no paid SEO tools, no
Search Console API dependency, just the deployed static contract we control.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit
from xml.etree import ElementTree as ET

REPO_ROOT = Path(__file__).resolve().parent.parent
BASE_URL = "https://kwalia.ai"
ESSAYS_JSON = REPO_ROOT / "data" / "essays.json"

CANONICAL_RE = re.compile(r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']', re.IGNORECASE)
HREFLANG_RE = re.compile(
    r'<link\s+rel=["\']alternate["\']\s+hreflang=["\']([^"\']+)["\']\s+href=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
KWALIA_ESSAY_URL_RE = re.compile(r"https://kwalia\.ai(?P<path>/essays/[^\"'<>\s)]+)")


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs):
        attrs_dict = dict(attrs)
        href = attrs_dict.get("href")
        if href:
            self.links.append((tag, href))


class EssayCardParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cards: list[dict[str, str]] = []
        self.current: dict[str, str] | None = None
        self.card_depth = 0
        self.capture_field: str | None = None
        self.capture_tag: str | None = None
        self.capture_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs):
        attrs_dict = dict(attrs)
        classes = set((attrs_dict.get("class") or "").split())

        if tag == "a" and "essay-card" in classes and self.current is None:
            self.current = {
                "href": attrs_dict.get("href", ""),
                "data_href_en": attrs_dict.get("data-href-en", ""),
                "data_href_es": attrs_dict.get("data-href-es", ""),
                "data_tags": attrs_dict.get("data-tags", ""),
            }
            self.card_depth = 1
            return

        if self.current is None:
            return

        self.card_depth += 1
        if tag == "h2":
            self.current["title_en"] = attrs_dict.get("data-en", "")
            self.current["title_es"] = attrs_dict.get("data-es", "")
            self.capture_field = "title_visible"
            self.capture_tag = tag
            self.capture_parts = []
        elif tag == "p" and "text-c2/70" in classes:
            self.current["subtitle_en"] = attrs_dict.get("data-en", "")
            self.current["subtitle_es"] = attrs_dict.get("data-es", "")
            self.capture_field = "subtitle_visible"
            self.capture_tag = tag
            self.capture_parts = []

    def handle_data(self, data: str):
        if self.current is not None and self.capture_field:
            self.capture_parts.append(data)

    def handle_endtag(self, tag: str):
        if self.current is None:
            return

        if self.capture_field and tag == self.capture_tag:
            self.current[self.capture_field] = normalize_text("".join(self.capture_parts))
            self.capture_field = None
            self.capture_tag = None
            self.capture_parts = []

        self.card_depth -= 1
        if self.card_depth == 0:
            self.cards.append(self.current)
            self.current = None


def has_non_ascii(value: str) -> bool:
    return any(ord(char) > 127 for char in value)


def normalize_text(value: str) -> str:
    return " ".join(value.split())


def load_essays() -> list[dict]:
    return json.loads(ESSAYS_JSON.read_text(encoding="utf-8"))


def load_slug_pairs() -> dict[str, dict[str, str]]:
    entries = load_essays()
    pairs_by_slug: dict[str, dict[str, str]] = {}
    for entry in entries:
        slug_data = entry.get("slug", {})
        if not isinstance(slug_data, dict):
            continue
        pair = {k: v for k, v in slug_data.items() if k in {"en", "es"} and v}
        for slug in pair.values():
            pairs_by_slug[slug] = pair
    return pairs_by_slug


def canonical_links(html: str) -> list[str]:
    return CANONICAL_RE.findall(html)


def hreflang_links(html: str) -> dict[str, str]:
    return {hreflang: href for hreflang, href in HREFLANG_RE.findall(html)}


def page_candidates_from_url_path(base_file: Path, url_path: str) -> list[Path]:
    decoded = unquote(url_path)
    if decoded.startswith("/"):
        target = REPO_ROOT / decoded.lstrip("/")
    else:
        target = base_file.parent / decoded

    candidates = [target]
    if decoded.endswith("/"):
        candidates = [target / "index.html"]
    elif not decoded.endswith(".html"):
        candidates.extend([Path(str(target) + ".html"), target / "index.html"])
    return candidates


def internal_page_exists(base_file: Path, url_path: str) -> bool:
    repo = REPO_ROOT.resolve()
    for candidate in page_candidates_from_url_path(base_file, url_path):
        resolved = candidate.resolve()
        if repo not in resolved.parents and resolved != repo:
            continue
        if candidate.exists():
            return True
    return False


def validate_page_links(path: Path, errors: list[str]) -> None:
    parser = LinkParser()
    html = path.read_text(encoding="utf-8", errors="replace")
    parser.feed(html)

    page_url = f"{BASE_URL}/{path.relative_to(REPO_ROOT).as_posix()}"
    if path.name == "index.html":
        page_url = page_url[: -len("index.html")]

    for tag, href in parser.links:
        if href.startswith(("mailto:", "tel:", "#", "javascript:", "data:")):
            continue
        parsed = urlsplit(urljoin(page_url, href))
        if parsed.netloc and parsed.netloc not in ("kwalia.ai", "www.kwalia.ai"):
            continue

        if has_non_ascii(href):
            errors.append(f"{path.relative_to(REPO_ROOT)} has non-ASCII href: {href}")

        if tag != "a":
            continue

        page_path = unquote(parsed.path)
        if not page_path:
            continue
        if page_path.endswith((".jpg", ".jpeg", ".png", ".webp", ".svg", ".css", ".js", ".ico", ".xml", ".txt", ".json", ".epub", ".pdf")):
            continue
        if not internal_page_exists(path, page_path):
            errors.append(f"{path.relative_to(REPO_ROOT)} links to missing internal page: {href}")

    for match in KWALIA_ESSAY_URL_RE.finditer(html):
        url_path = unquote(match.group("path"))
        if has_non_ascii(url_path):
            errors.append(f"{path.relative_to(REPO_ROOT)} embeds non-ASCII essay URL: https://kwalia.ai{url_path}")


def validate_canonicals(errors: list[str]) -> None:
    expected = {
        REPO_ROOT / "index.html": f"{BASE_URL}/",
        REPO_ROOT / "essays" / "index.html": f"{BASE_URL}/essays/",
    }

    for path, canonical in expected.items():
        html = path.read_text(encoding="utf-8")
        links = canonical_links(html)
        if links != [canonical]:
            errors.append(f"{path.relative_to(REPO_ROOT)} canonical mismatch: {links!r} != {[canonical]!r}")

    pairs_by_slug = load_slug_pairs()
    for path in sorted((REPO_ROOT / "essays").glob("*.html")):
        if path.name == "index.html":
            continue

        slug = path.stem
        html = path.read_text(encoding="utf-8")
        expected_canonical = f"{BASE_URL}/essays/{slug}.html"
        links = canonical_links(html)
        if links != [expected_canonical]:
            errors.append(f"{path.relative_to(REPO_ROOT)} canonical mismatch: {links!r} != {[expected_canonical]!r}")

        pair = pairs_by_slug.get(slug, {})
        if pair.get("en") and pair.get("es"):
            expected_alternates = {
                "en": f"{BASE_URL}/essays/{pair['en']}.html",
                "es": f"{BASE_URL}/essays/{pair['es']}.html",
                "x-default": f"{BASE_URL}/essays/{pair['en']}.html",
            }
            actual = hreflang_links(html)
            if actual != expected_alternates:
                errors.append(f"{path.relative_to(REPO_ROOT)} hreflang mismatch: {actual!r} != {expected_alternates!r}")


def validate_sitemap(errors: list[str]) -> None:
    for sitemap in sorted(REPO_ROOT.glob("sitemap*.xml")):
        tree = ET.parse(sitemap)
        for loc in tree.findall(".//{*}loc"):
            if not loc.text:
                continue
            url = loc.text.strip()
            parsed = urlsplit(url)
            if parsed.netloc != "kwalia.ai":
                continue
            if has_non_ascii(url):
                errors.append(f"{sitemap.name} contains non-ASCII URL: {url}")
            if sitemap.name == "sitemap-index.xml":
                continue
            if not internal_page_exists(REPO_ROOT / "index.html", parsed.path):
                errors.append(f"{sitemap.name} lists missing URL: {url}")


def validate_essay_listing_contract(errors: list[str]) -> None:
    index_path = REPO_ROOT / "essays" / "index.html"
    html = index_path.read_text(encoding="utf-8")
    parser = EssayCardParser()
    parser.feed(html)

    entries = load_essays()
    published_entries = [
        entry
        for entry in entries
        if entry.get("status") == "published"
        and isinstance(entry.get("slug"), dict)
        and entry["slug"].get("en")
    ]

    cards_by_slug: dict[str, dict[str, str]] = {}
    for card in parser.cards:
        href_en = card.get("data_href_en", "")
        slug = href_en.removesuffix(".html")
        if slug in cards_by_slug:
            errors.append(f"essays/index.html has duplicate essay card for slug: {slug}")
        cards_by_slug[slug] = card

    expected_slugs = {entry["slug"]["en"] for entry in published_entries}
    actual_slugs = set(cards_by_slug)
    for slug in sorted(expected_slugs - actual_slugs):
        errors.append(f"essays/index.html missing published essay card from data/essays.json: {slug}")
    for slug in sorted(actual_slugs - expected_slugs):
        errors.append(f"essays/index.html has essay card not published in data/essays.json: {slug}")

    for entry in published_entries:
        slug_data = entry["slug"]
        slug_en = slug_data["en"]
        slug_es = slug_data.get("es") or slug_en
        card = cards_by_slug.get(slug_en)
        if not card:
            continue

        expected_href_en = f"{slug_en}.html"
        expected_href_es = f"{slug_es}.html"
        if card.get("href") != expected_href_en:
            errors.append(f"essays/index.html card href mismatch for {slug_en}: {card.get('href')!r} != {expected_href_en!r}")
        if card.get("data_href_en") != expected_href_en:
            errors.append(f"essays/index.html data-href-en mismatch for {slug_en}: {card.get('data_href_en')!r} != {expected_href_en!r}")
        if card.get("data_href_es") != expected_href_es:
            errors.append(f"essays/index.html data-href-es mismatch for {slug_en}: {card.get('data_href_es')!r} != {expected_href_es!r}")

        tags = entry.get("tags") or []
        expected_tags = " ".join(tags)
        if card.get("data_tags") != expected_tags:
            errors.append(f"essays/index.html data-tags mismatch for {slug_en}: {card.get('data_tags')!r} != {expected_tags!r}")

        title = entry.get("title") or {}
        subtitle = entry.get("subtitle") or {}
        title_en = title.get("en", "")
        subtitle_en = subtitle.get("en", "")
        expected = {
            "title_en": normalize_text(title_en),
            "title_es": normalize_text(title.get("es") or title_en),
            "title_visible": normalize_text(title_en),
            "subtitle_en": normalize_text(subtitle_en),
            "subtitle_es": normalize_text(subtitle.get("es") or subtitle_en),
            "subtitle_visible": normalize_text(subtitle_en),
        }
        for field, expected_value in expected.items():
            actual_value = normalize_text(card.get(field, ""))
            if actual_value != expected_value:
                errors.append(f"essays/index.html {field} mismatch for {slug_en}: {actual_value!r} != {expected_value!r}")

    required_search_snippets = [
        "keys: ['title', 'excerpt', 'tags', 'href']",
        "ignoreLocation: true",
    ]
    for snippet in required_search_snippets:
        if snippet not in html:
            errors.append(f"essays/index.html search contract missing snippet: {snippet}")


def main() -> int:
    errors: list[str] = []
    validate_canonicals(errors)

    for path in sorted(REPO_ROOT.rglob("*.html")):
        if any(part.startswith(".") for part in path.relative_to(REPO_ROOT).parts):
            continue
        if "templates" in path.relative_to(REPO_ROOT).parts:
            continue
        validate_page_links(path, errors)

    validate_sitemap(errors)
    validate_essay_listing_contract(errors)

    if errors:
        print("Indexing contract FAILED:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("Indexing contract OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
