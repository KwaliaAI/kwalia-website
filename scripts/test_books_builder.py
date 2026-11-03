#!/usr/bin/env python3
"""Regression tests for catalogue selection, source mapping and migration proof."""
import copy
import hashlib
import json
import unittest

from build_books_json import ROOT, build_row, encode, generate, live_channels, presentation_for


class BooksBuilderTests(unittest.TestCase):
    def setUp(self):
        self.overlay = json.loads((ROOT / "data/books.overrides.json").read_bytes())
        self.row = {"title_id": "example", "title": "Approved title", "imprint": "kwalia-books",
                    "language": "eng", "isbn_eb": "9781917717724", "blurb_300": "Exact approved description.\nSecond paragraph.",
                    "price_eb_gbp": 4.99, "channel_delivery_status": {"bookwire": {"status": "live"}}}

    def test_baseline_exact_original_hash_and_eight_rows(self):
        self.assertEqual(len(self.overlay["legacy_rows"]), 8)
        self.assertEqual(hashlib.sha256(encode(self.overlay["legacy_rows"])).hexdigest(), self.overlay["baseline_sha256"])

    def test_import_is_not_channel_activation(self):
        for status in ("imported", "uploaded", "assets_uploaded", "submitted_for_review"):
            self.row["channel_delivery_status"]["bookwire"]["status"] = status
            self.row.update(lifecycle_stage="published", enable_for_sale=True)
            self.assertEqual(live_channels(self.row), [])

    def test_partial_kindle_with_stale_sale_flag(self):
        self.row.update(enable_for_sale=False, lifecycle_stage="production",
                        channel_delivery_status={"amazon-kdp": {"status": "partially_live"}},
                        draft_metadata={"kdp_format_status": {"ebook": "live", "paperback": "publishing"},
                                        "kdp_asins": {"ebook": "B0HQ569Y93", "paperback": "1917717717"}})
        channels = live_channels(self.row)
        self.assertEqual(channels, ["amazon-kdp"])
        book = build_row(self.row, self.overlay, channels)
        self.assertEqual([s["url"] for s in book["stores"]], ["https://www.amazon.com/dp/B0HQ569Y93"])

    def test_fiamma_and_translation_rows_excluded(self):
        fiamma = {**self.row, "title_id": "fiamma", "imprint": "fiamma-books"}
        spanish = {**self.row, "title_id": "example-es", "language": "spa"}
        books, _ = generate([self.row, fiamma, spanish], self.overlay)
        self.assertEqual([b["id"] for b in books], ["example"])

    def test_copy_prices_isbn_and_spanish_fallback(self):
        book = build_row(self.row, self.overlay, ["bookwire"])
        self.assertEqual(book["synopsis"], {"en": self.row["blurb_300"]})
        self.assertEqual(book["prices"], [{"type": "ebook", "amount": "£4.99"}])
        self.assertEqual(book["formats"], [{"type": "ebook", "isbn": "978-1-917717-72-4"}])
        self.assertEqual(book["coverImage"], {"en": "assets/9781917717724.jpg"})

    def test_bliss_kept_hidden_with_empty_stores(self):
        self.row.update(series_title="Kwalia Bliss", channel_delivery_status={},
                        isbn_audio=self.row.pop("isbn_eb"))
        books, _ = generate([self.row], self.overlay)
        self.assertIs(books[0]["siteVisible"], False)
        self.assertEqual(books[0]["stores"], [])
        self.assertEqual(books[0]["formats"][0]["type"], "audiobook")

    def test_hidden_reader_preserves_approved_story_links(self):
        old = next(r for r in self.overlay["legacy_rows"] if r["id"] == "your-constitution-claude")
        self.row["title_id"] = old["id"]
        book = build_row(self.row, self.overlay, [])
        self.assertEqual(book["stories"], old["stories"])
        self.assertIs(book["siteVisible"], False)

    def test_english_copy_override_refused(self):
        overlay = copy.deepcopy(self.overlay)
        overlay["presentation"]["example"] = {"synopsis": {"en": "Unauthorized"}}
        with self.assertRaisesRegex(ValueError, "cannot be overridden"):
            presentation_for("example", overlay)

    def test_committed_artifact_hashes(self):
        source = json.loads((ROOT / "data/books.source.json").read_bytes())
        for key, filename in (("books_sha256", "books.json"), ("overlay_sha256", "books.overrides.json")):
            self.assertEqual(source[key], hashlib.sha256((ROOT / "data" / filename).read_bytes()).hexdigest())
        self.assertEqual(len(source["catalogue_commit"]), 40)


if __name__ == "__main__":
    unittest.main()
