import os
import tempfile
import unittest

from build import qa


class TestQaOverlay(unittest.TestCase):
    def test_overlay_is_written_and_non_trivial(self):
        with tempfile.TemporaryDirectory() as d:
            path = qa.hotspot_overlay(os.path.join(d, "qa.png"))
            self.assertTrue(os.path.exists(path))
            self.assertGreater(os.path.getsize(path), 100_000)


class TestArtefactsOnDisk(unittest.TestCase):
    """Runs against dist/ after `python3 make_brochure.py`."""

    def setUp(self):
        self.html = os.path.join("dist", "Lake-Tree-Avenue.html")
        self.pdf = os.path.join("dist", "Lake-Tree-Avenue-eBrochure.pdf")
        if not (os.path.exists(self.html) and os.path.exists(self.pdf)):
            self.skipTest("run `python3 make_brochure.py` first")

    def test_html_within_budget(self):
        self.assertLess(os.path.getsize(self.html), 6 * 1024 * 1024)

    def test_pdf_within_budget(self):
        self.assertLess(os.path.getsize(self.pdf), 8 * 1024 * 1024)


if __name__ == "__main__":
    unittest.main()
