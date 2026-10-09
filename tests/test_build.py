import os
import unittest

from build import build_html, copy

DIST = "dist"
DOCS = "docs"


class TestArtefactsOnDisk(unittest.TestCase):
    """Runs against dist/ and docs/ after `python3 make_brochure.py`."""

    def setUp(self):
        self.html = os.path.join(DIST, "Lake-Tree-Avenue.html")
        if not os.path.exists(self.html):
            self.skipTest("run `python3 make_brochure.py` first")

    def test_html_within_budget(self):
        self.assertLess(os.path.getsize(self.html), 6 * 1024 * 1024)

    def test_a_pdf_is_built_for_every_language(self):
        for code in copy.LOCALES:
            path = os.path.join(DIST, build_html.PDF_NAMES[code])
            self.assertTrue(os.path.exists(path), path)
            self.assertLess(os.path.getsize(path), 8 * 1024 * 1024, path)

    def test_the_page_and_every_pdf_are_published(self):
        # The download link beside each document is relative, so the file
        # it names has to sit next to index.html or the link 404s.
        self.assertTrue(os.path.exists(os.path.join(DOCS, "index.html")))
        for code in copy.LOCALES:
            self.assertTrue(
                os.path.exists(os.path.join(DOCS, build_html.PDF_NAMES[code])),
                build_html.PDF_NAMES[code])

    def test_the_english_pdf_keeps_the_name_already_being_shared(self):
        # This link has been forwarded. Renaming it breaks every copy of
        # it that is already out there.
        self.assertEqual(build_html.PDF_NAMES["en"],
                         "Lake-Tree-Avenue-eBrochure.pdf")


if __name__ == "__main__":
    unittest.main()
