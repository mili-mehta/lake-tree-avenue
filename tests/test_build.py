import os
import unittest

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
