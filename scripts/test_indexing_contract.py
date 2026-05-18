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
        (tmp_root / "_redirects").write_text(
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


def main() -> int:
    validator = load_validator()
    test_org_author_id_reference_fails(validator)
    test_person_author_id_reference_passes(validator)
    test_template_public_essay_url_detection(validator)
    test_forced_broad_essay_redirect_fails(validator)
    print("Indexing contract regression tests OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
