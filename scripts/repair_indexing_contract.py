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
HREF_RE = re.compile(
    r"(?P<prefix>\b(?:href|data-href-en|data-href-es)=)(?P<quote>[\"'])(?P<value>[^\"']*)(?P=quote)"
)
OG_URL_RE = re.compile(
    r'(<meta\s+property=[\"\'"]og:url[\"\'"]\s+content=[\"\'"])([^\"\'"]*)([\"\'"])',
    re.IGNORECASE,
)
JSON_LD_BLOCK_RE = re.compile(
    r'(<script\s+type=["\']application/ld\+json["\']>\s*)(.*?)(\s*</script>)',
    re.IGNORECASE | re.DOTALL,
)
PAGE_PATH_RE = re.compile(
    r"(?P<prefix>[\"']page_path[\"']\s*:\s*)(?P<quote>[\"'])(?P<value>/essays/[^\"']+)(?P=quote)"
)
KWALIA_ESSAY_URL_RE = re.compile(r"https://kwalia\.ai(?P<path>/essays/[^\"'<>\s)]+)")
LEGACY_SLUGS = {
    "three-futures": "the-three-futures",
    "three-futures.html": "the-three-futures",
    "ya-eres-un-ciborg": "ya-eres-un-cyborg",
    "ya-eres-un-ciborg.html": "ya-eres-un-cyborg",
    "que-es-la-infraclase-permanente": "que-es-la-subclase-permanente",
    "que-es-la-infraclase-permanente.html": "que-es-la-subclase-permanente",
}

STABLE_ARTICLE_AUTHOR = {
    "@type": "Person",
    "@id": "https://kwalia.ai/#javier-del-puerto",
    "name": "Javier del Puerto",
    "url": "https://kwalia.ai",
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


def is_essay_url_path(path: Path, url_path: str) -> bool:
    decoded_path = unquote(url_path).split("?", 1)[0].split("#", 1)[0]
    if decoded_path.startswith("/"):
        return decoded_path.startswith("/essays/")
    return path.parent == REPO_ROOT / "essays"


def replace_legacy_slug(url_path: str) -> str:
    path_parts = url_path.rsplit("/", 1)
    filename = path_parts[-1]
    replacement = LEGACY_SLUGS.get(filename)
    if not replacement:
        return url_path
    return f"{path_parts[0]}/{replacement}" if len(path_parts) == 2 else replacement


def normalize_internal_href(path: Path, href: str) -> str:
    if not href or href.startswith(("mailto:", "tel:", "#", "javascript:", "data:")):
        return href

    parsed = urlsplit(href)
    if parsed.scheme and parsed.scheme not in ("http", "https"):
        return href
    if parsed.netloc and parsed.netloc not in ("kwalia.ai", "www.kwalia.ai"):
        return href

    decoded_path = unquote(parsed.path)
    original_path = decoded_path
    decoded_path = replace_legacy_slug(decoded_path)
    if decoded_path.endswith(".html") and is_essay_url_path(path, decoded_path):
        stripped = decoded_path[:-5]
        if local_page_exists_from_path(path, stripped):
            decoded_path = stripped

    normalized_path = strip_accents(decoded_path)

    if normalized_path.endswith(".html") and is_essay_url_path(path, normalized_path):
        stripped = normalized_path[:-5]
        if local_page_exists_from_path(path, stripped):
            normalized_path = stripped

    if normalized_path == original_path:
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


def normalize_page_paths(path: Path, html: str) -> tuple[str, int]:
    changed = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal changed
        page_path = match.group("value")
        normalized = normalize_internal_href(path, page_path)
        if normalized != page_path:
            changed += 1
        return f"{match.group('prefix')}{match.group('quote')}{normalized}{match.group('quote')}"

    return PAGE_PATH_RE.sub(replace, html), changed


def normalize_embedded_kwalia_urls(path: Path, html: str) -> tuple[str, int]:
    changed = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal changed
        parsed = urlsplit(match.group(0))
        url_path = unquote(parsed.path)
        original_path = url_path
        url_path = replace_legacy_slug(url_path)
        if url_path.endswith(".html") and is_essay_url_path(path, url_path):
            stripped = url_path[:-5]
            if local_page_exists_from_path(path, stripped):
                url_path = stripped
        normalized_path = strip_accents(url_path)
        if normalized_path.endswith(".html") and is_essay_url_path(path, normalized_path):
            stripped = normalized_path[:-5]
            if local_page_exists_from_path(path, stripped):
                normalized_path = stripped
        if normalized_path == original_path:
            return match.group(0)
        if not local_page_exists_from_path(path, normalized_path):
            return match.group(0)
        changed += 1
        safe_path = quote(normalized_path, safe="/:._-~%")
        return urlunsplit((parsed.scheme, parsed.netloc, safe_path, parsed.query, parsed.fragment))

    return KWALIA_ESSAY_URL_RE.sub(replace, html), changed


def alternates_for_slug(slug: str, pairs_by_slug: dict[str, dict[str, str]]) -> list[tuple[str, str]]:
    pair = pairs_by_slug.get(slug, {})
    en_slug = pair.get("en")
    es_slug = pair.get("es")
    if not en_slug or not es_slug:
        return []

    return [
        ("en", f"{BASE_URL}/essays/{en_slug}"),
        ("es", f"{BASE_URL}/essays/{es_slug}"),
        ("x-default", f"{BASE_URL}/essays/{en_slug}"),
    ]


def repair_og_url(html: str, canonical_url: str) -> tuple[str, int]:
    repaired, count = OG_URL_RE.subn(rf"\1{canonical_url}\3", html, count=1)
    return repaired, count


def normalize_jsonld_string(value: str, canonical_url: str) -> tuple[str, int]:
    html_url = f"{canonical_url}.html"
    if value == html_url or value.startswith(f"{html_url}#"):
        return canonical_url + value[len(html_url) :], 1
    return value, 0


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


def jsonld_node_index(value: object) -> dict[str, dict]:
    nodes: dict[str, dict] = {}
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


def article_author_needs_repair(author: object, nodes_by_id: dict[str, dict]) -> bool:
    if not isinstance(author, (dict, list)):
        return True
    return any(author_type != "Person" for author_type in author_type_values(author, nodes_by_id))


def update_jsonld_object(value: object, canonical_url: str, nodes_by_id: dict[str, dict]) -> int:
    changed = 0
    article_id = f"{canonical_url}#article"

    if isinstance(value, dict):
        for key, item in list(value.items()):
            if isinstance(item, str):
                normalized, item_changed = normalize_jsonld_string(item, canonical_url)
                if item_changed:
                    value[key] = normalized
                    changed += item_changed
            elif isinstance(item, (dict, list)):
                changed += update_jsonld_object(item, canonical_url, nodes_by_id)

        if value.get("@type") == "Article":
            if value.get("url") != canonical_url:
                value["url"] = canonical_url
                changed += 1
            if value.get("@id") != article_id:
                value["@id"] = article_id
                changed += 1
            author = value.get("author")
            if article_author_needs_repair(author, nodes_by_id):
                value["author"] = dict(STABLE_ARTICLE_AUTHOR)
                changed += 1

    elif isinstance(value, list):
        for item in value:
            changed += update_jsonld_object(item, canonical_url, nodes_by_id)

    return changed


def repair_article_jsonld(html: str, canonical_url: str) -> tuple[str, int]:
    changed = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal changed
        raw_json = match.group(2).strip()
        try:
            parsed = json.loads(raw_json)
        except json.JSONDecodeError:
            return match.group(0)

        block_changes = update_jsonld_object(parsed, canonical_url, jsonld_node_index(parsed))
        if not block_changes:
            return match.group(0)

        changed += block_changes
        serialized = json.dumps(parsed, ensure_ascii=False, indent=2)
        return f"{match.group(1)}{serialized}{match.group(3)}"

    repaired = JSON_LD_BLOCK_RE.sub(replace, html)
    return repaired, changed


def repair_file(path: Path, canonical_url: str, alternates: list[tuple[str, str]]) -> tuple[bool, int]:
    original = path.read_text(encoding="utf-8")
    repaired = insert_indexing_block(original, canonical_url, alternates)
    repaired, og_changes = repair_og_url(repaired, canonical_url)
    repaired, jsonld_changes = repair_article_jsonld(repaired, canonical_url)
    repaired, href_changes = normalize_internal_hrefs(path, repaired)
    repaired, page_path_changes = normalize_page_paths(path, repaired)
    repaired, embedded_url_changes = normalize_embedded_kwalia_urls(path, repaired)
    href_changes += embedded_url_changes + page_path_changes + og_changes + jsonld_changes
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
        canonical_url = f"{BASE_URL}/essays/{slug}"
        alternates = alternates_for_slug(slug, pairs_by_slug)
        fixed, hrefs = repair_file(path, canonical_url, alternates)
        changed_files += int(fixed)
        changed_hrefs += hrefs

    print(f"Repaired indexing contract in {changed_files} file(s).")
    print(f"Normalized {changed_hrefs} internal href(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
