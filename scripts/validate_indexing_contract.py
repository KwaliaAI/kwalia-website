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
from ast import literal_eval
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
OG_URL_RE = re.compile(r'<meta\s+property=["\']og:url["\']\s+content=["\']([^"\']+)["\']', re.IGNORECASE)
JSON_LD_RE = re.compile(r'<script\s+type=["\']application/ld\+json["\']>\s*(.*?)\s*</script>', re.IGNORECASE | re.DOTALL)
KWALIA_ESSAY_URL_RE = re.compile(r"https://kwalia\.ai(?P<path>/essays/[^\"'<>\s)]+)")
RAW_PUBLIC_ESSAY_HTML_RE = re.compile(
    r"https://kwalia\.ai/essays/[^\"'<>\s)]+\.html(?:#[^\"'<>\s)]*)?"
    r"|(?<![A-Za-z0-9:/._-])/essays/[^\"'<>\s)]+\.html(?:#[^\"'<>\s)]*)?"
)
BAD_ESSAY_REDIRECT_RE = re.compile(r"^/essays/[^ \t]*\.html[ \t]+/essays/[ \t]+301\b", re.MULTILINE)
QUERY_ALIAS_PATHS = ("/essays/?filter=creativity", "/essays/?filter=digital")
PDF_CANONICAL_PATH = "/assets/your-constitution-claude-press-release.pdf"
PDF_NOINDEX_HEADER = "noindex"


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs):
        attrs_dict = dict(attrs)
        href = attrs_dict.get("href")
        if href:
            self.links.append((tag, href))


class MetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.values: dict[tuple[str, str], str] = {}

    def handle_starttag(self, tag: str, attrs):
        if tag != "meta":
            return
        attrs_dict = dict(attrs)
        content = attrs_dict.get("content", "")
        for attr in ("name", "property"):
            key = attrs_dict.get(attr)
            if key:
                self.values[(attr, key.lower())] = content


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


def markdown_source_slugs() -> set[str]:
    slugs: set[str] = set()
    for path in (REPO_ROOT / "content" / "essays").glob("**/*.md"):
        text = path.read_text(encoding="utf-8", errors="replace")
        match = re.search(r"^slug:\s*[\"']?([^\"'\n]+)", text, re.MULTILINE)
        slugs.add(match.group(1).strip() if match else path.stem)
    return slugs


def canonical_links(html: str) -> list[str]:
    return CANONICAL_RE.findall(html)


def hreflang_links(html: str) -> dict[str, str]:
    return {hreflang: href for hreflang, href in HREFLANG_RE.findall(html)}


def og_url(html: str) -> str | None:
    match = OG_URL_RE.search(html)
    return match.group(1) if match else None


def meta_values(html: str) -> dict[tuple[str, str], str]:
    parser = MetaParser()
    parser.feed(html)
    return parser.values


def jsonld_values(html: str) -> list[object]:
    values: list[object] = []
    for block in JSON_LD_RE.findall(html):
        try:
            parsed = json.loads(block)
        except json.JSONDecodeError:
            continue
        values.append(parsed)
    return values


def jsonld_objects(html: str) -> list[dict]:
    objects: list[dict] = []
    for parsed in jsonld_values(html):
        if isinstance(parsed, dict) and isinstance(parsed.get("@graph"), list):
            objects.extend(item for item in parsed["@graph"] if isinstance(item, dict))
        elif isinstance(parsed, dict):
            objects.append(parsed)
        elif isinstance(parsed, list):
            objects.extend(item for item in parsed if isinstance(item, dict))
    return objects


def jsonld_type_values(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def jsonld_id_aliases(node_id: object) -> list[str]:
    if not isinstance(node_id, str) or not node_id:
        return []

    aliases = [node_id]
    parsed = urlsplit(node_id)
    if parsed.fragment:
        aliases.append(f"#{parsed.fragment}")
    if node_id.startswith("#"):
        aliases.append(f"{BASE_URL}/{node_id}")

    deduped: list[str] = []
    for alias in aliases:
        if alias not in deduped:
            deduped.append(alias)
    return deduped


def jsonld_nodes(value: object):
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


def jsonld_node_index(html: str) -> dict[str, dict]:
    nodes: dict[str, dict] = {}
    for parsed in jsonld_values(html):
        for node in jsonld_nodes(parsed):
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


def author_type_values(author: object, nodes_by_id: dict[str, dict], seen: set[str] | None = None) -> list[str]:
    seen = seen or set()
    if isinstance(author, list):
        values: list[str] = []
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


def article_non_person_author_types(article: dict, nodes_by_id: dict[str, dict]) -> list[str]:
    bad_types: list[str] = []
    authors = article.get("author")
    if isinstance(authors, dict):
        authors = [authors]
    if not isinstance(authors, list):
        return bad_types

    for author in authors:
        for author_type in author_type_values(author, nodes_by_id):
            if author_type != "Person" and author_type not in bad_types:
                bad_types.append(author_type)
    return bad_types


def article_has_organization_author(article: dict, nodes_by_id: dict[str, dict] | None = None) -> bool:
    nodes_by_id = nodes_by_id or {}
    return bool(article_non_person_author_types(article, nodes_by_id))


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


def is_public_essay_html_path(url_path: str) -> bool:
    return url_path.startswith("/essays/") and url_path.endswith(".html")


def validate_page_links(path: Path, errors: list[str]) -> None:
    parser = LinkParser()
    html = path.read_text(encoding="utf-8", errors="replace")
    parser.feed(html)

    for match in RAW_PUBLIC_ESSAY_HTML_RE.finditer(html):
        errors.append(f"{path.relative_to(REPO_ROOT)} contains raw .html essay URL: {match.group(0)}")

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
        if is_public_essay_html_path(page_path):
            errors.append(f"{path.relative_to(REPO_ROOT)} links to .html essay URL: {href}")
        if page_path.endswith((".jpg", ".jpeg", ".png", ".webp", ".svg", ".css", ".js", ".ico", ".xml", ".txt", ".json", ".epub", ".pdf")):
            continue
        if not internal_page_exists(path, page_path):
            errors.append(f"{path.relative_to(REPO_ROOT)} links to missing internal page: {href}")

    for match in KWALIA_ESSAY_URL_RE.finditer(html):
        url = match.group(0)
        url_path = unquote(urlsplit(url).path)
        if has_non_ascii(url_path):
            errors.append(f"{path.relative_to(REPO_ROOT)} embeds non-ASCII essay URL: https://kwalia.ai{url_path}")
        if is_public_essay_html_path(url_path):
            errors.append(f"{path.relative_to(REPO_ROOT)} embeds .html essay URL: {url}")


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
        actual_og = og_url(html)
        if actual_og != canonical:
            errors.append(f"{path.relative_to(REPO_ROOT)} og:url mismatch: {actual_og!r} != {canonical!r}")

    pairs_by_slug = load_slug_pairs()
    generated_slugs = markdown_source_slugs()
    for path in sorted((REPO_ROOT / "essays").glob("*.html")):
        if path.name == "index.html":
            continue

        slug = path.stem
        html = path.read_text(encoding="utf-8")
        metas = meta_values(html)
        jsonld_node_by_id = jsonld_node_index(html)
        expected_canonical = f"{BASE_URL}/essays/{slug}"
        links = canonical_links(html)
        if links != [expected_canonical]:
            errors.append(f"{path.relative_to(REPO_ROOT)} canonical mismatch: {links!r} != {[expected_canonical]!r}")
        actual_og = metas.get(("property", "og:url")) or og_url(html)
        if actual_og != expected_canonical:
            errors.append(f"{path.relative_to(REPO_ROOT)} og:url mismatch: {actual_og!r} != {expected_canonical!r}")

        expected_og_image = None
        og_asset = REPO_ROOT / "assets" / "og" / f"{slug}.jpg"
        if og_asset.exists():
            expected_og_image = f"{BASE_URL}/assets/og/{slug}.jpg"
            actual_og_image = metas.get(("property", "og:image"))
            if actual_og_image != expected_og_image:
                errors.append(
                    f"{path.relative_to(REPO_ROOT)} og:image mismatch: {actual_og_image!r} != {expected_og_image!r}"
                )
            if metas.get(("property", "og:image:width")) != "1200":
                errors.append(f"{path.relative_to(REPO_ROOT)} missing og:image:width=1200")
            if metas.get(("property", "og:image:height")) != "630":
                errors.append(f"{path.relative_to(REPO_ROOT)} missing og:image:height=630")
            if metas.get(("name", "twitter:image")) != expected_og_image:
                errors.append(
                    f"{path.relative_to(REPO_ROOT)} twitter:image mismatch: {metas.get(('name', 'twitter:image'))!r} != {expected_og_image!r}"
                )

        article = None
        faq_page = None
        for obj in jsonld_objects(html):
            if obj.get("@type") == "Article":
                article = obj
            elif obj.get("@type") == "FAQPage":
                faq_page = obj
        if not article:
            errors.append(f"{path.relative_to(REPO_ROOT)} missing Article JSON-LD")
        else:
            expected_article_id = f"{expected_canonical}#article"
            if article.get("url") != expected_canonical:
                errors.append(
                    f"{path.relative_to(REPO_ROOT)} Article url mismatch: {article.get('url')!r} != {expected_canonical!r}"
                )
            if article.get("@id") != expected_article_id:
                errors.append(
                    f"{path.relative_to(REPO_ROOT)} Article @id mismatch: {article.get('@id')!r} != {expected_article_id!r}"
                )
            non_person_author_types = article_non_person_author_types(article, jsonld_node_by_id)
            if non_person_author_types:
                errors.append(
                    f"{path.relative_to(REPO_ROOT)} Article author is non-Person JSON-LD type: "
                    f"{', '.join(non_person_author_types)}"
                )
            if expected_og_image and slug in generated_slugs:
                image = article.get("image")
                image_url = image.get("url") if isinstance(image, dict) else None
                if image_url != expected_og_image:
                    errors.append(
                        f"{path.relative_to(REPO_ROOT)} Article image mismatch: {image_url!r} != {expected_og_image!r}"
                    )

        faq_path = REPO_ROOT / "data" / "faq" / f"{slug}.json"
        if faq_path.exists():
            expected_faq_id = f"{expected_canonical}#faq"
            if not faq_page:
                errors.append(f"{path.relative_to(REPO_ROOT)} missing FAQPage JSON-LD for {faq_path.relative_to(REPO_ROOT)}")
            elif faq_page.get("@id") != expected_faq_id:
                errors.append(
                    f"{path.relative_to(REPO_ROOT)} FAQPage @id mismatch: {faq_page.get('@id')!r} != {expected_faq_id!r}"
                )

        pair = pairs_by_slug.get(slug, {})
        if pair.get("en") and pair.get("es"):
            expected_alternates = {
                "en": f"{BASE_URL}/essays/{pair['en']}",
                "es": f"{BASE_URL}/essays/{pair['es']}",
                "x-default": f"{BASE_URL}/essays/{pair['en']}",
            }
            actual = hreflang_links(html)
            if actual != expected_alternates:
                errors.append(f"{path.relative_to(REPO_ROOT)} hreflang mismatch: {actual!r} != {expected_alternates!r}")


def validate_query_aliases(errors: list[str]) -> None:
    essays_html = (REPO_ROOT / "essays" / "index.html").read_text(encoding="utf-8")
    canonical = f"{BASE_URL}/essays/"
    if canonical_links(essays_html) != [canonical]:
        errors.append("essays/index.html canonical drifted away from the query alias contract")
    for alias in QUERY_ALIAS_PATHS:
        if urlsplit(alias).path != "/essays/":
            errors.append(f"unexpected query alias path: {alias}")


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
            if parsed.query:
                errors.append(f"{sitemap.name} lists a query URL: {url}")
            if parsed.path.startswith("/essays/") and parsed.path.endswith(".html"):
                errors.append(f"{sitemap.name} still lists .html essay URL: {url}")
            if not internal_page_exists(REPO_ROOT / "index.html", parsed.path):
                errors.append(f"{sitemap.name} lists missing URL: {url}")


def parse_toml_scalar(raw_value: str) -> str:
    value = raw_value.strip()
    try:
        parsed = literal_eval(value)
    except (SyntaxError, ValueError):
        return value.strip("\"'")
    return parsed if isinstance(parsed, str) else str(parsed)


def netlify_header_blocks() -> list[dict[str, object]]:
    netlify_toml = (REPO_ROOT / "netlify.toml").read_text(encoding="utf-8")
    blocks: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    in_values = False

    for line in netlify_toml.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "[[headers]]":
            current = {"for": "", "values": {}}
            blocks.append(current)
            in_values = False
            continue
        if current is None:
            continue
        if stripped == "[headers.values]":
            in_values = True
            continue
        if stripped.startswith("["):
            in_values = False
            continue
        if "=" not in stripped:
            continue

        key, raw_value = stripped.split("=", 1)
        key = key.strip()
        value = parse_toml_scalar(raw_value)
        if in_values:
            values = current["values"]
            assert isinstance(values, dict)
            values[key] = value
        elif key == "for":
            current["for"] = value

    return blocks


def validate_netlify_policy(errors: list[str]) -> None:
    matches = [block for block in netlify_header_blocks() if block.get("for") == PDF_CANONICAL_PATH]
    if not matches:
        errors.append("netlify.toml is missing the PDF noindex header policy")
        return

    values = matches[-1].get("values", {})
    if not isinstance(values, dict):
        errors.append("netlify.toml has an invalid PDF header policy")
        return
    if "Link" in values:
        errors.append("netlify.toml must not canonicalize the PDF to the download shim")
    x_robots = values.get("X-Robots-Tag")
    tokens = [token.strip().lower() for token in str(x_robots or "").split(",")]
    if PDF_NOINDEX_HEADER not in tokens:
        errors.append("netlify.toml has an incorrect PDF noindex header policy")


def validate_redirect_policy(errors: list[str]) -> None:
    redirects = (REPO_ROOT / "_redirects").read_text(encoding="utf-8")
    if BAD_ESSAY_REDIRECT_RE.search(redirects):
        errors.append("_redirects contains a broad essay .html redirect to /essays/")


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
        slug = href_en
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

        expected_href_en = slug_en
        expected_href_es = slug_es
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
    validate_query_aliases(errors)

    for path in sorted(REPO_ROOT.rglob("*.html")):
        if any(part.startswith(".") for part in path.relative_to(REPO_ROOT).parts):
            continue
        if "templates" in path.relative_to(REPO_ROOT).parts:
            continue
        validate_page_links(path, errors)

    validate_sitemap(errors)
    validate_netlify_policy(errors)
    validate_redirect_policy(errors)
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
