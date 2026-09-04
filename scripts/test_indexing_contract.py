#!/usr/bin/env python3
"""Focused regression tests for the local indexing contract validator."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory

SCRIPT_DIR = Path(__file__).resolve().parent
VALIDATOR_PATH = SCRIPT_DIR / "validate_indexing_contract.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_indexing_contract", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def article_from_html(validator, html: str) -> dict:
    for obj in validator.jsonld_objects(html):
        if obj.get("@type") == "Article":
            return obj
    raise AssertionError("fixture is missing Article JSON-LD")


def author_types_for_html(validator, html: str) -> list[str]:
    article = article_from_html(validator, html)
    return validator.article_non_person_author_types(article, validator.jsonld_node_index(html))


def test_org_author_id_reference_fails(validator) -> None:
    for author_id in ("#org", "https://kwalia.ai/#org"):
        html = """
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@graph": [
        {
          "@type": "Article",
          "@id": "https://kwalia.ai/essays/example#article",
          "author": {"@id": "__AUTHOR_ID__"}
        },
        {
          "@type": "Organization",
          "@id": "https://kwalia.ai/#org",
          "name": "Kwalia"
        }
      ]
    }
    </script>
    """.replace("__AUTHOR_ID__", author_id)
        assert author_types_for_html(validator, html) == ["Organization"]


def test_person_author_id_reference_passes(validator) -> None:
    html = """
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@graph": [
        {
          "@type": "Article",
          "@id": "https://kwalia.ai/essays/example#article",
          "author": {"@id": "https://kwalia.ai/#javier-del-puerto"}
        },
        {
          "@type": "Person",
          "@id": "https://kwalia.ai/#javier-del-puerto",
          "name": "Javier del Puerto"
        }
      ]
    }
    </script>
    """
    assert author_types_for_html(validator, html) == []


def test_template_public_essay_url_detection(validator) -> None:
    assert validator.TEMPLATE_PUBLIC_ESSAY_URL_RE.search('/essays/${slug}')
    assert validator.TEMPLATE_PUBLIC_ESSAY_URL_RE.search('https://kwalia.ai/essays/${slug}.html')
    assert not validator.TEMPLATE_PUBLIC_ESSAY_URL_RE.search("'/essays/' + slug")


def test_forced_broad_essay_redirect_fails(validator) -> None:
    original_root = validator.REPO_ROOT
    with TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        (tmp_root / "essays").mkdir()
        (tmp_root / "essays" / "example.html").write_text("<html></html>", encoding="utf-8")
        (tmp_root / "_redirects").write_text(
            "/essays/example.html /essays/example 301!\n"
            "/essays/foo.html /essays/ 301!\n"
            "/essays/%24%7Bslug%7D.html /essays/ 301!\n",
            encoding="utf-8",
        )
        validator.REPO_ROOT = tmp_root
        errors: list[str] = []
        try:
            validator.validate_redirect_policy(errors)
        finally:
            validator.REPO_ROOT = original_root

    assert errors == ["_redirects contains a broad essay .html redirect to /essays/: /essays/foo.html"]


def test_missing_exact_essay_html_redirect_fails(validator) -> None:
    original_root = validator.REPO_ROOT
    with TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        (tmp_root / "essays").mkdir()
        (tmp_root / "essays" / "example.html").write_text("<html></html>", encoding="utf-8")
        (tmp_root / "_redirects").write_text("", encoding="utf-8")
        validator.REPO_ROOT = tmp_root
        errors: list[str] = []
        try:
            validator.validate_redirect_policy(errors)
        finally:
            validator.REPO_ROOT = original_root

    assert errors == ["_redirects missing canonical essay redirect: /essays/example.html /essays/example 301!"]


def test_essay_redirect_target_html_fails(validator) -> None:
    original_root = validator.REPO_ROOT
    with TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        (tmp_root / "essays").mkdir()
        (tmp_root / "essays" / "example.html").write_text("<html></html>", encoding="utf-8")
        (tmp_root / "_redirects").write_text(
            "/essays/example.html /essays/example 301!\n"
            "/essays/old.html /essays/new.html 301\n",
            encoding="utf-8",
        )
        validator.REPO_ROOT = tmp_root
        errors: list[str] = []
        try:
            validator.validate_redirect_policy(errors)
        finally:
            validator.REPO_ROOT = original_root

    assert errors == ["_redirects points essay redirect at .html URL: /essays/old.html -> /essays/new.html"]


def test_public_llms_txt_html_link_fails(validator) -> None:
    original_root = validator.REPO_ROOT
    with TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        (tmp_root / "llms.txt").write_text(
            "- [Essay](https://kwalia.ai/essays/example.html)\n",
            encoding="utf-8",
        )
        validator.REPO_ROOT = tmp_root
        errors: list[str] = []
        try:
            validator.validate_public_text_surfaces(errors)
        finally:
            validator.REPO_ROOT = original_root

    assert errors == ["llms.txt contains raw .html essay URL: https://kwalia.ai/essays/example.html"]


def test_stale_mailerlite_form_asset_fails(validator) -> None:
    original_root = validator.REPO_ROOT
    with TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        html_path = tmp_root / "index.html"
        html_path.write_text(
            "<script>fetch('https://assets.mailerlite.com/jsonp/1588336/forms/131498498498498254/ta498.js')</script>",
            encoding="utf-8",
        )
        validator.REPO_ROOT = tmp_root
        errors: list[str] = []
        try:
            validator.validate_page_links(html_path, errors)
        finally:
            validator.REPO_ROOT = original_root

    assert errors == [
        "index.html contains stale MailerLite form asset URL: "
        "https://assets.mailerlite.com/jsonp/1588336/forms/131498498498498254/ta498.js"
    ]


def test_sitemap_missing_essay_url_fails(validator) -> None:
    original_root = validator.REPO_ROOT
    with TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        (tmp_root / "essays").mkdir()
        (tmp_root / "essays" / "example.html").write_text("<html></html>", encoding="utf-8")
        (tmp_root / "sitemap-essays.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>\n',
            encoding="utf-8",
        )
        validator.REPO_ROOT = tmp_root
        errors: list[str] = []
        try:
            validator.validate_sitemap(errors)
        finally:
            validator.REPO_ROOT = original_root

    assert errors == ["sitemap-essays.xml missing essay URL: https://kwalia.ai/essays/example"]


def test_sitemap_missing_essays_index_url_fails(validator) -> None:
    original_root = validator.REPO_ROOT
    with TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        (tmp_root / "essays").mkdir()
        (tmp_root / "essays" / "index.html").write_text("<html></html>", encoding="utf-8")
        (tmp_root / "sitemap-essays.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>\n',
            encoding="utf-8",
        )
        validator.REPO_ROOT = tmp_root
        errors: list[str] = []
        try:
            validator.validate_sitemap(errors)
        finally:
            validator.REPO_ROOT = original_root

    assert errors == ["sitemap-essays.xml missing essays index URL: https://kwalia.ai/essays/"]


def test_asset_pdf_wildcard_noindex_header_required(validator) -> None:
    original_root = validator.REPO_ROOT
    with TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        (tmp_root / "netlify.toml").write_text(
            """
[[headers]]
  for = "/assets/one.pdf"

  [headers.values]
    X-Robots-Tag = "noindex"
""",
            encoding="utf-8",
        )
        validator.REPO_ROOT = tmp_root
        errors: list[str] = []
        try:
            validator.validate_netlify_policy(errors)
        finally:
            validator.REPO_ROOT = original_root

    assert errors == ["netlify.toml is missing the asset PDF noindex header policy: /assets/*.pdf"]


def test_asset_pdf_wildcard_noindex_header_passes(validator) -> None:
    original_root = validator.REPO_ROOT
    with TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        (tmp_root / "netlify.toml").write_text(
            """
[[headers]]
  for = "/assets/*.pdf"

  [headers.values]
    X-Robots-Tag = "noindex"
""",
            encoding="utf-8",
        )
        validator.REPO_ROOT = tmp_root
        errors: list[str] = []
        try:
            validator.validate_netlify_policy(errors)
        finally:
            validator.REPO_ROOT = original_root

    assert errors == []


def test_tracking_query_cleanup_policy_required(validator) -> None:
    original_root = validator.REPO_ROOT
    original_file = validator.TRACKING_QUERY_CLEANUP_FILE
    with TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        (tmp_root / "netlify.toml").write_text("", encoding="utf-8")
        validator.REPO_ROOT = tmp_root
        validator.TRACKING_QUERY_CLEANUP_FILE = (
            tmp_root / "netlify" / "edge-functions" / "tracking-query-cleanup.ts"
        )
        errors: list[str] = []
        try:
            validator.validate_tracking_query_cleanup_policy(errors)
        finally:
            validator.REPO_ROOT = original_root
            validator.TRACKING_QUERY_CLEANUP_FILE = original_file

    assert errors == [
        "netlify.toml is missing the tracking query cleanup edge function: tracking-query-cleanup /",
        "tracking query cleanup edge function is missing: netlify/edge-functions/tracking-query-cleanup.ts",
    ]


def test_core_reading_paths_missing_section_fails(validator) -> None:
    original_root = validator.REPO_ROOT
    with TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        (tmp_root / "essays").mkdir()
        (tmp_root / "essays" / "index.html").write_text("<html></html>", encoding="utf-8")
        validator.REPO_ROOT = tmp_root
        errors: list[str] = []
        try:
            validator.validate_core_reading_paths(errors)
        finally:
            validator.REPO_ROOT = original_root

    assert errors == ["essays/index.html is missing the core reading paths section"]


def test_core_reading_paths_required_links_pass(validator) -> None:
    original_root = validator.REPO_ROOT
    with TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        essays_dir = tmp_root / "essays"
        essays_dir.mkdir()
        links = "\n".join(
            f'<a href="{slug}">{slug}</a>' for slug in validator.CORE_READING_PATH_SLUGS
        )
        item_urls = "\n".join(
            f'"https://kwalia.ai/essays/{slug}"' for slug in validator.CORE_READING_PATH_SLUGS
        )
        for slug in validator.CORE_READING_PATH_SLUGS:
            (essays_dir / f"{slug}.html").write_text("<html></html>", encoding="utf-8")
        (essays_dir / "index.html").write_text(
            f"""
<section id="core-reading-paths">
  {links}
</section>

                <div id="essays-list"></div>
<script type="application/ld+json">{{"@type": "ItemList", "name": "Core Kwalia reading paths", "itemListElement": [{item_urls}]}}</script>
""",
            encoding="utf-8",
        )
        validator.REPO_ROOT = tmp_root
        errors: list[str] = []
        try:
            validator.validate_core_reading_paths(errors)
        finally:
            validator.REPO_ROOT = original_root

    assert errors == []


def test_homepage_core_entry_link_required(validator) -> None:
    original_root = validator.REPO_ROOT
    with TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        (tmp_root / "index.html").write_text('<a href="/essays/">Essays</a>', encoding="utf-8")
        validator.REPO_ROOT = tmp_root
        errors: list[str] = []
        try:
            validator.validate_homepage_core_entry_link(errors)
        finally:
            validator.REPO_ROOT = original_root

    assert errors == ["index.html is missing the homepage link to /essays/#core-reading-paths"]


def test_unknown_related_frontmatter_fails(validator) -> None:
    original_root = validator.REPO_ROOT
    original_essays_json = validator.ESSAYS_JSON
    with TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        content_dir = tmp_root / "content" / "essays" / "en"
        content_dir.mkdir(parents=True)
        (tmp_root / "data").mkdir()
        validator.ESSAYS_JSON = tmp_root / "data" / "essays.json"
        validator.ESSAYS_JSON.write_text(
            '[{"id": "known-essay", "slug": {"en": "known-essay"}}]',
            encoding="utf-8",
        )
        (content_dir / "example.md").write_text(
            """---
id: example
slug: example
related:
  - known-essay
  - missing-essay
---
Body.
""",
            encoding="utf-8",
        )
        validator.REPO_ROOT = tmp_root
        errors: list[str] = []
        try:
            validator.validate_related_frontmatter(errors)
        finally:
            validator.REPO_ROOT = original_root
            validator.ESSAYS_JSON = original_essays_json

    assert errors == ["content/essays/en/example.md related essay is unknown: missing-essay"]


def main() -> int:
    validator = load_validator()
    test_org_author_id_reference_fails(validator)
    test_person_author_id_reference_passes(validator)
    test_template_public_essay_url_detection(validator)
    test_forced_broad_essay_redirect_fails(validator)
    test_missing_exact_essay_html_redirect_fails(validator)
    test_essay_redirect_target_html_fails(validator)
    test_public_llms_txt_html_link_fails(validator)
    test_stale_mailerlite_form_asset_fails(validator)
    test_sitemap_missing_essay_url_fails(validator)
    test_sitemap_missing_essays_index_url_fails(validator)
    test_asset_pdf_wildcard_noindex_header_required(validator)
    test_asset_pdf_wildcard_noindex_header_passes(validator)
    test_tracking_query_cleanup_policy_required(validator)
    test_core_reading_paths_missing_section_fails(validator)
    test_core_reading_paths_required_links_pass(validator)
    test_homepage_core_entry_link_required(validator)
    test_unknown_related_frontmatter_fails(validator)
    print("Indexing contract regression tests OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
